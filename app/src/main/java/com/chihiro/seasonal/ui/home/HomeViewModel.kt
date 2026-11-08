package com.chihiro.seasonal.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.chihiro.seasonal.data.FoodRepository
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class HomeViewModel(
    private val foodRepository: FoodRepository,
) : ViewModel() {
    private val mutableUiState = MutableStateFlow<HomeUiState>(HomeUiState.Loading)
    val uiState: StateFlow<HomeUiState> = mutableUiState.asStateFlow()

    private var loadJob: Job? = null

    init {
        loadFoods()
    }

    fun retry() {
        loadFoods()
    }

    private fun loadFoods() {
        loadJob?.cancel()
        loadJob = viewModelScope.launch {
            mutableUiState.value = HomeUiState.Loading
            try {
                val foods = foodRepository.getFoods()
                coroutineContext.ensureActive()
                mutableUiState.value =
                    if (foods.isEmpty()) HomeUiState.Empty else HomeUiState.Content(foods)
            } catch (cancellation: CancellationException) {
                throw cancellation
            } catch (_: Exception) {
                coroutineContext.ensureActive()
                mutableUiState.value = HomeUiState.Error
            }
        }
    }
}
