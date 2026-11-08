package com.chihiro.seasonal.ui.home

import com.chihiro.seasonal.domain.FoodSummary

sealed interface HomeUiState {
    data object Loading : HomeUiState

    data object Empty : HomeUiState

    data class Content(val foods: List<FoodSummary>) : HomeUiState

    data object Error : HomeUiState
}
