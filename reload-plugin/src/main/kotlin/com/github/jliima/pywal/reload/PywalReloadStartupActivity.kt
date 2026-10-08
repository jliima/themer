package com.github.jliima.pywal.reload

import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.openapi.project.Project
import com.intellij.openapi.startup.ProjectActivity

class PywalReloadStartupActivity : ProjectActivity {
    override suspend fun execute(project: Project) {
        try {
            PywalReloadServer.start()
        } catch (e: Exception) {
            thisLogger().warn("Pywal reload server failed to start: ${e.message}")
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
}
