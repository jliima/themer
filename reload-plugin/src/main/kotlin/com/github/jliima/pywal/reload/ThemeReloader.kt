package com.github.jliima.pywal.reload

import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.databind.node.ObjectNode
import com.intellij.ide.actions.QuickChangeLookAndFeel
import com.intellij.ide.ui.LafManager
import com.intellij.ide.ui.UITheme
import com.intellij.ide.ui.laf.UIThemeLookAndFeelInfo
import com.intellij.ide.ui.laf.UIThemeLookAndFeelInfoImpl
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.application.PathManager
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.editor.colors.EditorColorsManager
import com.intellij.openapi.editor.colors.impl.EditorColorsSchemeImpl
import com.intellij.openapi.util.JDOMUtil
import java.io.File

object ThemeReloader {
    private val log = thisLogger()
    private val mapper = ObjectMapper()

    // Paths to project source files
    private val mappingFile = File(
        System.getProperty("user.home"),
        "JetBrainsProjects/jetbrains-pywal-theme/theme/ui-mapping.json"
    )
    private val iclsTemplate = File(
        System.getProperty("user.home"),
        "JetBrainsProjects/jetbrains-pywal-theme/pywal_color_scheme.icls"
    )

    // Palette: Themer's export for the applied theme and variant, else pywal's colors.json
    private val themerColors = File(System.getProperty("user.home"), ".cache/themer/jetbrains.json")
    private val walColors = File(System.getProperty("user.home"), ".cache/wal/colors.json")

    private fun colorsFile(): File = if (themerColors.exists()) themerColors else walColors

    fun reload(): Result<String> = runCatching {
        val messages = mutableListOf<String>()
        ApplicationManager.getApplication().invokeAndWait {
            reloadUiTheme()?.let { messages += it }
            reloadEditorScheme()?.let { messages += it }
        }
        messages.joinToString("; ").ifEmpty { "ok" }
    }

    private fun reloadUiTheme(): String? {
        val colorsFile = colorsFile()
        if (!colorsFile.exists()) {
            log.warn("colors.json not found: $colorsFile")
            return "colors.json missing"
        }
        if (!mappingFile.exists()) {
            log.warn("ui-mapping.json not found: $mappingFile")
            return "ui-mapping.json missing"
        }

        val themeJson = buildThemeJson(colorsFile, mappingFile)
        val theme = themeJson.byteInputStream().use { stream ->
            @Suppress("UnstableApiUsage")
            UITheme.Companion.loadTempThemeFromJson(stream, "pywal-theme")
        }

        val lafInfo: UIThemeLookAndFeelInfo = UIThemeLookAndFeelInfoImpl(theme)
        QuickChangeLookAndFeel.switchLafAndUpdateUI(LafManager.getInstance(), lafInfo, false)
        log.info("Pywal UI theme reloaded from $colorsFile + $mappingFile")
        return "UI theme reloaded"
    }

    private fun reloadEditorScheme(): String? {
        val colorsFile = colorsFile()
        if (!colorsFile.exists()) {
            log.warn("colors.json not found: $colorsFile")
            return "colors.json missing"
        }
        if (!iclsTemplate.exists()) {
            log.warn("ICLS template not found: $iclsTemplate")
            return "ICLS template missing"
        }

        // Build the processed ICLS by substituting {varName} with bare hex values
        val palette = buildPalette(colorsFile, stripHash = true)
        val processed = iclsTemplate.readText()
            .replace(Regex("""\{(\w+)\}""")) { match ->
                palette[match.groupValues[1]] ?: match.value
            }

        // Write processed ICLS to the IDE config colors directory
        val configPath = PathManager.getConfigPath()
        val outputIcls = File(configPath, "colors/pywal-color-scheme.icls")
        outputIcls.parentFile.mkdirs()
        outputIcls.writeText(processed)

        // Load and apply the scheme
        val colorsManager = EditorColorsManager.getInstance()
        val parentScheme = colorsManager.getScheme(palette.getValue("parentScheme"))
            ?: colorsManager.allSchemes.firstOrNull()
            ?: return "no parent scheme available"
        val scheme = EditorColorsSchemeImpl(parentScheme)
        scheme.readExternal(JDOMUtil.load(outputIcls))

        colorsManager.addColorScheme(scheme)
        colorsManager.setGlobalScheme(scheme)
        log.info("Pywal editor scheme reloaded from $iclsTemplate")
        return "editor scheme reloaded"
    }

    /**
     * Builds a flat color palette from colors.json.
     * @param stripHash if true, returns bare hex (for ICLS); if false, keeps # (for theme JSON)
     */
    private fun buildPalette(colorsFile: File, stripHash: Boolean = false): Map<String, String> {
        val root = mapper.readTree(colorsFile)
        val palette = mutableMapOf<String, String>()
        root.get("special")?.fields()?.forEach { (k, v) ->
            palette[k] = if (stripHash) v.asText().removePrefix("#") else v.asText()
        }
        root.get("colors")?.fields()?.forEach { (k, v) ->
            palette[k] = if (stripHash) v.asText().removePrefix("#") else v.asText()
        }
        // Same derived names as scripts/palette.py: the template's parent scheme and the UI theme's dark flag
        val dark = isDark(palette["background"] ?: "000000")
        palette["parentScheme"] = if (dark) "Darcula" else "Default"
        palette["isDark"] = dark.toString()
        return palette
    }

    /** True when the WCAG relative luminance of a #rrggbb / rrggbb background is below 0.5. */
    private fun isDark(hex: String): Boolean {
        val h = hex.removePrefix("#")
        fun channel(i: Int): Double {
            val s = h.substring(i, i + 2).toInt(16) / 255.0
            return if (s <= 0.03928) s / 12.92 else Math.pow((s + 0.055) / 1.055, 2.4)
        }
        return 0.2126 * channel(0) + 0.7152 * channel(2) + 0.0722 * channel(4) < 0.5
    }

    /**
     * Combines colors.json palette with ui-mapping.json to produce a full IntelliJ theme JSON.
     */
    private fun buildThemeJson(colorsFile: File, mappingFile: File): String {
        val palette = buildPalette(colorsFile)
        val mapping = mapper.readTree(mappingFile) as ObjectNode

        // Build colors section from full palette
        val colorsNode = mapper.createObjectNode()
        palette.filterValues { it.startsWith("#") }.forEach { (k, v) -> colorsNode.put(k, v) }

        // Assemble final theme object: mapping fields + injected colors section
        val theme = mapper.createObjectNode().apply {
            put("name",         mapping.get("name").asText())
            put("dark",         palette.getValue("isDark").toBoolean())
            put("editorScheme", mapping.get("editorScheme").asText())
            set<ObjectNode>("colors", colorsNode)
            set<ObjectNode>("ui",     mapping.get("ui") as ObjectNode)
            mapping.get("icons")?.let { set<ObjectNode>("icons", it as ObjectNode) }
        }

        return mapper.writeValueAsString(theme)
    }
}
