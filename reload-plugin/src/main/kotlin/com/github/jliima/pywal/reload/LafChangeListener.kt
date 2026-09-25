package com.github.jliima.pywal.reload

import com.intellij.ide.ui.LafManager
import com.intellij.ide.ui.LafManagerListener
import com.intellij.openapi.diagnostic.thisLogger

/** Re-applies Copilot color overrides whenever the Look and Feel changes (including pywal live reloads). */
class LafChangeListener : LafManagerListener {
    override fun lookAndFeelChanged(source: LafManager) {
        try {
            CopilotColorPatcher.apply()
        } catch (e: Exception) {
            thisLogger().warn("Copilot color patching failed: ${e.message}")
        }
    }
}
