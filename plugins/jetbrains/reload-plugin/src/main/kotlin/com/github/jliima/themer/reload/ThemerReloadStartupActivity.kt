package com.github.jliima.themer.reload

import com.intellij.ide.ui.LafManager
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.application.PathManager
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.project.Project
import com.intellij.openapi.startup.ProjectActivity
import java.io.File
import java.util.concurrent.atomic.AtomicBoolean

class ThemerReloadStartupActivity : ProjectActivity {
    companion object {
        /** The fonts are applied once per IDE session, when the first project opens. */
        private val fontsApplied = AtomicBoolean(false)
    }

    override suspend fun execute(project: Project) {
        try {
            ThemerReloadServer.start()
        } catch (e: Exception) {
            thisLogger().warn("Themer reload server failed to start: ${e.message}")
        }
        try {
            switchOnce()
        } catch (e: Exception) {
            thisLogger().warn("Switching to the Themer theme failed: ${e.message}")
        }
        if (fontsApplied.compareAndSet(false, true)) {
            ApplicationManager.getApplication().invokeLater {
                try {
                    FontReloader.reload()
                } catch (e: Exception) {
                    thisLogger().warn("Applying the Themer fonts failed: ${e.message}")
                }
            }
        }
        try {
            CopilotColorPatcher.apply()
        } catch (e: Exception) {
            thisLogger().warn("Copilot color patching failed: ${e.message}")
        }
        try {
            VcsLogGraphColorPatcher.apply()
        } catch (e: Exception) {
            thisLogger().warn("VCS log graph color patching failed: ${e.message}")
        }
    }

    /**
     * Once per IDE config folder, selects the Themer theme and scheme. An IDE that last ran another theme falls
     * back to a stock one, and a later themer apply cannot fix that while the IDE is closed.
     */
    private fun switchOnce() {
        val marker = File(PathManager.getConfigPath(), "options/themer-theme-selected")
        if (marker.exists() || !ThemeReloader.hasFiles()) return
        if (LafManager.getInstance().currentUIThemeLookAndFeel?.id != ThemeReloader.THEME_ID) {
            ThemeReloader.reload().onFailure { throw it }
        }
        marker.parentFile.mkdirs()
        marker.writeText("")
    }
}
