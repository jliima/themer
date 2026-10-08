package com.github.jliima.themer.reload

import com.intellij.openapi.diagnostic.thisLogger
import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.util.concurrent.Executors

object ThemerReloadServer {
    private val PORT = System.getenv("THEMER_RELOAD_PORT")?.toIntOrNull() ?: 9988
    private val log = thisLogger()
    private var server: HttpServer? = null

    fun start() {
        if (server != null) return

        server = HttpServer.create(InetSocketAddress("127.0.0.1", PORT), 0).apply {
            createContext("/reload") { exchange ->
                if (exchange.requestMethod != "POST") {
                    val body = "Method Not Allowed".toByteArray()
                    exchange.sendResponseHeaders(405, body.size.toLong())
                    exchange.responseBody.use { it.write(body) }
                    return@createContext
                }
                val result = ThemeReloader.reload()
                val (code, body) = if (result.isSuccess) {
                    200 to """{"status":"ok","message":"${result.getOrDefault("ok")}"}"""
                } else {
                    500 to """{"status":"error","message":"${result.exceptionOrNull()?.message}"}"""
                }
                val bytes = body.toByteArray()
                exchange.responseHeaders.add("Content-Type", "application/json")
                exchange.sendResponseHeaders(code, bytes.size.toLong())
                exchange.responseBody.use { it.write(bytes) }
            }
            createContext("/health") { exchange ->
                val body = """{"status":"ok"}""".toByteArray()
                exchange.responseHeaders.add("Content-Type", "application/json")
                exchange.sendResponseHeaders(200, body.size.toLong())
                exchange.responseBody.use { it.write(body) }
            }
            executor = Executors.newSingleThreadExecutor { r ->
                Thread(r, "themer-reload-server").also { it.isDaemon = true }
            }
            start()
        }

        log.info("Themer reload server started on port $PORT")
    }

    fun stop() {
        server?.stop(0)
        server = null
    }
}
