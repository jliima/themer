package com.github.jliima.themer.reload

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

/**
 * Applies what `themer apply` rendered: the UI theme JSON from ~/.cache/themer/jetbrains, the editor scheme
 * Themer wrote into this IDE's config folder (colors/Themer.icls) and the fonts (FontReloader). Nothing is computed here; the colors come from
 * the Themer templates in the dotfiles.
 */
object ThemeReloader {
    const val THEME_ID = "themer-theme"
    const val SCHEME_NAME = "Themer"

    private val log = thisLogger()

    private val themeFile = File(System.getProperty("user.home"), ".cache/themer/jetbrains/themer.theme.json")

    private fun schemeFile(): File = File(PathManager.getConfigPath(), "colors/$SCHEME_NAME.icls")

    /** True when Themer has rendered both files for this IDE. */
    fun hasFiles(): Boolean = themeFile.exists() && schemeFile().exists()

    fun reload(): Result<String> = runCatching {
        val messages = mutableListOf<String>()
        ApplicationManager.getApplication().invokeAndWait {
            reloadUiTheme()?.let { messages += it }
            reloadEditorScheme()?.let { messages += it }
            FontReloader.reload()?.let { messages += it }
        }
        messages.joinToString("; ").ifEmpty { "ok" }
    }

    private fun reloadUiTheme(): String? {
        if (!themeFile.exists()) {
            log.warn("Themer UI theme not found: $themeFile")
            return "themer.theme.json missing, run themer apply"
        }

        val theme = themeFile.inputStream().use { stream ->
            @Suppress("UnstableApiUsage")
            UITheme.Companion.loadTempThemeFromJson(stream, THEME_ID)
        }

        val lafInfo: UIThemeLookAndFeelInfo = UIThemeLookAndFeelInfoImpl(theme)
        QuickChangeLookAndFeel.switchLafAndUpdateUI(LafManager.getInstance(), lafInfo, false)
        log.info("Themer UI theme reloaded from $themeFile")
        return null
    }

    private fun reloadEditorScheme(): String? {
        val file = schemeFile()
        if (!file.exists()) {
            log.warn("Themer editor scheme not found: $file")
            return "${file.name} missing, run themer apply"
        }

        val root = JDOMUtil.load(file)
        val colorsManager = EditorColorsManager.getInstance()
        val parentScheme = colorsManager.getScheme(root.getAttributeValue("parent_scheme") ?: "Darcula")
            ?: colorsManager.allSchemes.firstOrNull()
            ?: return "no parent scheme available"
        val scheme = EditorColorsSchemeImpl(parentScheme)
        scheme.readExternal(root)

        colorsManager.addColorScheme(scheme)
        colorsManager.setGlobalScheme(scheme)
        log.info("Themer editor scheme reloaded from $file")
        return null
    }
}
