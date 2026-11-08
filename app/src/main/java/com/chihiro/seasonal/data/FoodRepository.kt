package com.chihiro.seasonal.data

import com.chihiro.seasonal.domain.FoodSummary

interface FoodRepository {
    suspend fun getFoods(): List<FoodSummary>
}

/** Placeholder data source until the source data format and bundled-data loader are defined. */
class EmptyFoodRepository : FoodRepository {
    override suspend fun getFoods(): List<FoodSummary> = emptyList()
}
