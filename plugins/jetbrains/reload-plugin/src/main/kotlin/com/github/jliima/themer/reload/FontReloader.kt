package com.github.jliima.themer.reload

import com.intellij.ide.ui.LafManager
import com.intellij.ide.ui.UISettings
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.editor.EditorFactory
import com.intellij.openapi.editor.colors.EditorColorsManager
import com.intellij.openapi.editor.colors.EditorFontCache
import com.intellij.openapi.editor.colors.impl.AppEditorFontOptions
import com.intellij.openapi.editor.colors.impl.EditorColorsManagerImpl
import com.intellij.openapi.editor.colors.impl.FontPreferencesImpl
import java.io.File
import java.util.Properties

/**
 * Applies the fonts `themer apply` rendered to ~/.cache/themer/jetbrains/fonts.properties (target "JetBrains fonts"):
 *
 *   editor.font=JetBrains Mono     editor font family (Settings > Editor > Font)
 *   editor.font.size=15            its size
 *   ui.font=Inter                  UI font (Settings > Appearance > Use custom font)
 *   ui.font.size=0                 its size; 0 turns the custom UI font off
 *
 * A missing key leaves that setting alone. Only what differs is changed, so an unchanged file costs nothing.
 * Call on the EDT.
 */
object FontReloader {
    private val log = thisLogger()

    private val file = File(System.getProperty("user.home"), ".cache/themer/jetbrains/fonts.properties")

    fun reload(): String? {
        if (!file.exists()) return null
        val props = Properties().apply { file.reader().use { load(it) } }
        val changed = listOf(applyEditorFont(props), applyUiFont(props))
        if (changed.any { it }) log.info("Themer fonts applied from $file")
        return null
    }

    private fun applyEditorFont(props: Properties): Boolean {
        val options = AppEditorFontOptions.getInstance()
        val prefs = FontPreferencesImpl()
        options.fontPreferences.copyTo(prefs)
        val family = props.getProperty("editor.font")?.trim()?.ifEmpty { null } ?: prefs.fontFamily
        val size = props.getProperty("editor.font.size")?.trim()?.toFloatOrNull()?.takeIf { it > 0 }
            ?: prefs.getSize2D(prefs.fontFamily)
        if (family == prefs.fontFamily && size == prefs.getSize2D(family)) return false

        if (family != prefs.fontFamily) {
            prefs.clearFonts()
            prefs.addFontFamily(family)
        }
        prefs.setFontSize(family, size)
        options.update(prefs)

        EditorFontCache.getInstance().reset()
        val colors = EditorColorsManager.getInstance()
        (colors as? EditorColorsManagerImpl)?.schemeChangedOrSwitched(colors.globalScheme)
        EditorFactory.getInstance().refreshAllEditors()
        return true
    }

    private fun applyUiFont(props: Properties): Boolean {
        val size = props.getProperty("ui.font.size")?.trim()?.toFloatOrNull() ?: return false
        val face = props.getProperty("ui.font")?.trim().orEmpty()
        val ui = UISettings.getInstance()
        val override = size > 0 && face.isNotEmpty()
        if (override == ui.overrideLafFonts && (!override || (face == ui.fontFace && size == ui.fontSize2D))) {
            return false
        }

        ui.overrideLafFonts = override
        if (override) {
            ui.fontFace = face
            ui.fontSize2D = size
        }
        ui.fireUISettingsChanged()
        LafManager.getInstance().updateUI()
        return true
    }
}
