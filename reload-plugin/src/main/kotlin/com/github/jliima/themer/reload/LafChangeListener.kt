package com.github.jliima.themer.reload

import com.intellij.ide.ui.LafManager
import com.intellij.ide.ui.LafManagerListener
import com.intellij.openapi.diagnostic.thisLogger

/** Re-applies Copilot and VCS log color overrides whenever the Look and Feel changes (including live reloads). */
class LafChangeListener : LafManagerListener {
    override fun lookAndFeelChanged(source: LafManager) {
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
