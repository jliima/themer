plugins {
    id("org.jetbrains.kotlin.jvm") version "2.3.0"
    id("org.jetbrains.intellij.platform") version "2.13.1"
}

group = providers.gradleProperty("pluginGroup").get()
version = providers.gradleProperty("pluginVersion").get()

repositories {
    mavenCentral()
    intellijPlatform {
        defaultRepositories()
    }
}

dependencies {
    intellijPlatform {
        intellijIdeaUltimate("2026.1")
    }
}

intellijPlatform {
    pluginConfiguration {
        id = "com.github.jliima.themer.reload"
        name = "Themer Theme Reloader"
        version = providers.gradleProperty("pluginVersion").get()
        ideaVersion {
            sinceBuild = "261"
        }
    }
    buildSearchableOptions = false
}

kotlin {
    jvmToolchain(17)
}
