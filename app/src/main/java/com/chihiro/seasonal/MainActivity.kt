package com.chihiro.seasonal

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.chihiro.seasonal.ui.home.HomeScreen
import com.chihiro.seasonal.ui.home.HomeViewModel

class MainActivity : ComponentActivity() {
    private val homeViewModel: HomeViewModel by lazy {
        val repository = (application as SeasonalApplication).appContainer.foodRepository
        ViewModelProvider(
            this,
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                    require(modelClass.isAssignableFrom(HomeViewModel::class.java))
                    return HomeViewModel(repository) as T
                }
            },
        )[HomeViewModel::class.java]
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            val state by homeViewModel.uiState.collectAsStateWithLifecycle()
            HomeScreen(state = state, onRetry = homeViewModel::retry)
        }
    }
}
