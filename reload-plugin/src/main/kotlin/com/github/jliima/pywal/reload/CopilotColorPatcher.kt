package com.github.jliima.pywal.reload

import com.intellij.ide.plugins.PluginManagerCore
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.extensions.PluginId
import com.intellij.ui.JBColor
import java.awt.Color
import java.lang.reflect.Field
import java.lang.reflect.Modifier
import java.util.IdentityHashMap
import java.util.function.Supplier
import javax.swing.UIManager

/**
 * Lets the theme recolor the GitHub Copilot plugin, whose chat UI uses hardcoded colors instead of theme keys.
 *
 * Theme keys under `Copilot.Palette.*`, `Copilot.Style.*` and `Copilot.Chat.*` (see ui-mapping.json) are resolved
 * to static color fields inside the Copilot plugin:
 *
 * - `Copilot.Palette.grey4`              -> `CopilotPalette.grey4`
 * - `Copilot.Palette.Background.chatBox` -> `CopilotPalette$Background.chatBox`
 * - `Copilot.Style.CodingAgent.PanelBackground` -> `Style$Colors$CodingAgent.PanelBackground`
 * - `Copilot.Chat.UserBubble.Dark`       -> `UserBubbleColors.Dark` (see [chatClasses])
 *
 * Swing `JBColor` fields get a supplier that reads the theme key on every paint, so they follow theme changes.
 * Compose color fields are `static final long` values and are overwritten directly; if the JIT has already
 * inlined one, an IDE restart is needed for that color to change. Keys missing from the theme restore the
 * plugin's original colors.
 */
object CopilotColorPatcher {
    private val log = thisLogger()

    private const val COPILOT_PLUGIN_ID = "com.github.copilot"
    private const val KEY_PREFIX = "Copilot."
    private const val PALETTE_CLASS = "com.github.copilot.style.CopilotPalette"
    private const val STYLE_CLASS = "com.github.copilot.style.Style\$Colors"
    private const val HARNESS_PACKAGE = "com.github.copilot.agentHarness.ui.conversation"

    private val chatClasses = mapOf(
        "UserBubble" to "$HARNESS_PACKAGE.renderer.usermessage.UserBubbleColors",
        "Chip" to "$HARNESS_PACKAGE.renderer.usermessage.ChipColors",
        "ToolCall" to "$HARNESS_PACKAGE.renderer.toolcall.ToolCallColors",
        "UserInput" to "$HARNESS_PACKAGE.renderer.toolcall.askuser.UserInputColors",
        "ScrollToBottom" to "$HARNESS_PACKAGE.ScrollToBottomColors",
        "ErrorBanner" to "$HARNESS_PACKAGE.renderer.worktree.ErrorBannerColors",
    )

    /** Theme key currently driving each patched JBColor; read by the installed suppliers. */
    private val jbColorKeys = IdentityHashMap<JBColor, String>()

    /** Original value of each patched Compose color field, used when its key leaves the theme. */
    private val originalLongs = mutableMapOf<Field, Long>()

    private val jbColorFunc: Field by lazy {
        JBColor::class.java.getDeclaredField("func").apply { isAccessible = true }
    }

    private val unsafe: sun.misc.Unsafe by lazy {
        val field = sun.misc.Unsafe::class.java.getDeclaredField("theUnsafe").apply { isAccessible = true }
        field.get(null) as sun.misc.Unsafe
    }

    /** Applies all `Copilot.*` theme keys. Safe to call repeatedly; does nothing if Copilot is not installed. */
    @Synchronized
    fun apply(): String? {
        val loader = PluginManagerCore.getPlugin(PluginId.getId(COPILOT_PLUGIN_ID))?.pluginClassLoader ?: return null

        val themeKeys = UIManager.getDefaults().keys.toList()
            .filterIsInstance<String>()
            .filter { it.startsWith(KEY_PREFIX) }

        var patched = 0
        val appliedLongs = mutableSetOf<Field>()
        for (key in themeKeys) {
            val field = resolveField(key.removePrefix(KEY_PREFIX), loader) ?: continue
            val color = UIManager.getColor(key) ?: continue
            try {
                when (field.type) {
                    JBColor::class.java -> patchJBColor(field, key)
                    java.lang.Long.TYPE -> patchLong(field, color).also { appliedLongs += field }
                    else -> continue
                }
                patched++
            } catch (e: Exception) {
                log.warn("Could not patch Copilot color $key: ${e.message}")
            }
        }

        // Restore Compose colors whose key is no longer in the theme
        (originalLongs.keys - appliedLongs).forEach { writeLong(it, originalLongs.getValue(it)) }

        log.info("Patched $patched Copilot colors")
        return "Copilot colors patched ($patched)"
    }

    private fun resolveField(path: String, loader: ClassLoader): Field? {
        val segments = path.split('.')
        if (segments.size < 2) return null
        val fieldName = segments.last()
        val classSegments = segments.subList(1, segments.size - 1)
        val className = when (segments.first()) {
            "Palette" -> PALETTE_CLASS + classSegments.joinToString("") { "$$it" }
            "Style" -> STYLE_CLASS + classSegments.joinToString("") { "$$it" }
            "Chat" -> classSegments.singleOrNull()?.let { chatClasses[it] }
            else -> null
        } ?: return null

        return try {
            Class.forName(className, true, loader).getDeclaredField(fieldName)
                .takeIf { Modifier.isStatic(it.modifiers) }
                ?.apply { isAccessible = true }
        } catch (_: ReflectiveOperationException) {
            null
        }
    }

    private fun patchJBColor(field: Field, key: String) {
        val jbColor = field.get(null) as? JBColor ?: return
        if (jbColorKeys.put(jbColor, key) != null) return

        // Snapshot the original behaviour before replacing its supplier
        val original = JBColor.lazy(snapshotSupplier(jbColor))
        jbColorFunc.set(jbColor, Supplier<Color> {
            jbColorKeys[jbColor]?.let { UIManager.getColor(it) } ?: original
        })
    }

    private fun snapshotSupplier(jbColor: JBColor): Supplier<Color> {
        @Suppress("UNCHECKED_CAST")
        val func = jbColorFunc.get(jbColor) as Supplier<Color>?
        if (func != null) return func
        val light = jbColor.readField("defaultColor") as Color? ?: Color(jbColor.rgb, true)
        val dark = jbColor.readField("darkColor") as Color? ?: light
        val fixed = JBColor(light, dark)
        val name = jbColor.readField("name") as String?
        return if (name != null) Supplier { JBColor.namedColor(name, fixed) } else Supplier { fixed }
    }

    private fun JBColor.readField(name: String): Any? =
        JBColor::class.java.getDeclaredField(name).apply { isAccessible = true }.get(this)

    private fun patchLong(field: Field, color: Color) {
        originalLongs.getOrPut(field) { field.getLong(null) }
        writeLong(field, composeColor(color))
    }

    /** Packs an sRGB color the way `androidx.compose.ui.graphics.Color(Int)` does. */
    private fun composeColor(color: Color): Long = (color.rgb.toLong() and 0xFFFFFFFFL) shl 32

    @Suppress("DEPRECATION")
    private fun writeLong(field: Field, value: Long) {
        unsafe.putLong(unsafe.staticFieldBase(field), unsafe.staticFieldOffset(field), value)
    }
}
