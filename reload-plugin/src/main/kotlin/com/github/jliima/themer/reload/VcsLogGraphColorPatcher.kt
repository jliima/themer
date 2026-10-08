package com.github.jliima.themer.reload

import com.intellij.ide.plugins.PluginManagerCore
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.diagnostic.thisLogger
import com.intellij.ui.JBColor
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
import java.util.function.IntFunction
import javax.swing.UIManager

/**
 * Lets the theme pick the VCS log graph branch colors, which the IDE derives from branch name hashes.
 *
 * Theme keys `VersionControl.Log.Graph.color1..N` (see the UI theme template in the dotfiles) form an ordered palette. Branches get
 * the next unused palette entry in the order the graph first paints them, so the topmost branches get the first
 * colors; the palette wraps around when it runs out. Without any such keys the IDE's own colors are used.
 *
 * Works by swapping the color cache of the internal `DefaultColorGenerator` service for [PaletteColorMap].
 */
object VcsLogGraphColorPatcher {
    private val log = thisLogger()

    private const val GENERATOR_CLASS = "com.intellij.vcs.log.graph.DefaultColorGenerator"
    private val colorKey = Regex("""VersionControl\.Log\.Graph\.color(\d+)""")

    /** Palette theme keys in order; read by the colors handed out by [PaletteColorMap]. */
    @Volatile
    private var paletteKeys: List<String> = emptyList()

    @Synchronized
    fun apply(): String? {
        paletteKeys = UIManager.getDefaults().keys.toList()
            .filterIsInstance<String>()
            .mapNotNull { key -> colorKey.matchEntire(key)?.let { it.groupValues[1].toInt() to key } }
            .sortedBy { it.first }
            .map { it.second }

        val generatorClass = findClass(GENERATOR_CLASS) ?: return null
        val generator = ApplicationManager.getApplication().getService(generatorClass) ?: return null
        val field = generatorClass.getDeclaredField("colorMap").apply { isAccessible = true }
        val current = field.get(generator)
        if (current is PaletteColorMap) {
            current.clear()
        } else {
            @Suppress("UNCHECKED_CAST")
            val map = PaletteColorMap().apply { putAll(current as Map<Int, JBColor>) }
            field.set(generator, map)
        }

        log.info("VCS log graph palette has ${paletteKeys.size} colors")
        return "VCS log graph colors (${paletteKeys.size})"
    }

    /** The generator lives in a platform content module that may have its own class loader. */
    private fun findClass(name: String): Class<*>? {
        val loaders = mutableListOf<ClassLoader?>(javaClass.classLoader)
        loaders += PluginManagerCore.getPlugin(PluginManagerCore.CORE_ID)?.pluginClassLoader
        try {
            val pluginSet = PluginManagerCore::class.java.getMethod("getPluginSet").invoke(PluginManagerCore)
            val modules = pluginSet.javaClass.getMethod("getEnabledModules").invoke(pluginSet) as List<*>
            modules.filterNotNull().mapTo(loaders) {
                it.javaClass.getMethod("getPluginClassLoader").invoke(it) as ClassLoader?
            }
        } catch (e: ReflectiveOperationException) {
            log.debug("Could not list platform modules: ${e.message}")
        }
        for (loader in loaders.filterNotNull().distinct()) {
            try {
                return Class.forName(name, true, loader)
            } catch (_: ClassNotFoundException) {
            }
        }
        log.warn("Could not find $name")
        return null
    }

    /** Color cache that hands out palette colors in first-use order, falling back to the IDE's generator. */
    private class PaletteColorMap : Int2ObjectOpenHashMap<JBColor>() {
        private var nextIndex = 0

        override fun computeIfAbsent(key: Int, mappingFunction: IntFunction<out JBColor>): JBColor {
            get(key)?.let { return it }
            if (paletteKeys.isEmpty()) return mappingFunction.apply(key).also { put(key, it) }

            val index = nextIndex++
            val fallback = mappingFunction.apply(key)
            val color = JBColor.lazy {
                val keys = paletteKeys
                if (keys.isEmpty()) fallback else UIManager.getColor(keys[index % keys.size]) ?: fallback
            }
            put(key, color)
            return color
        }

        override fun clear() {
            super.clear()
            nextIndex = 0
        }
    }
}
