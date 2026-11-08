package com.chihiro.seasonal

import android.app.Application
import com.chihiro.seasonal.data.AppContainer

class SeasonalApplication : Application() {
    val appContainer: AppContainer by lazy { AppContainer() }
}
