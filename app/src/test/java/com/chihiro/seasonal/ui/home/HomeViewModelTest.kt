package com.chihiro.seasonal.ui.home

import com.chihiro.seasonal.data.FoodRepository
import com.chihiro.seasonal.domain.FoodSummary
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.withContext
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class HomeViewModelTest {
    @Before
    fun setUp() {
        Dispatchers.setMain(StandardTestDispatcher())
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun emptyRepositoryTransitionsFromLoadingToEmpty() = runTest {
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        val viewModel = HomeViewModel(FakeFoodRepository { emptyList() })

        assertEquals(HomeUiState.Loading, viewModel.uiState.value)
        runCurrent()

        assertEquals(HomeUiState.Empty, viewModel.uiState.value)
    }

    @Test
    fun repositoryItemsAreExposedAsContent() = runTest {
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        val food = FoodSummary(id = "food-1", name = "りんご")
        val viewModel = HomeViewModel(FakeFoodRepository { listOf(food) })

        runCurrent()

        assertEquals(HomeUiState.Content(listOf(food)), viewModel.uiState.value)
    }

    @Test
    fun failureCanBeRetriedAndLoadsAgain() = runTest {
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        var attempts = 0
        val food = FoodSummary(id = "food-1", name = "りんご")
        val repository = FakeFoodRepository {
            attempts++
            if (attempts == 1) error("temporary failure") else listOf(food)
        }
        val viewModel = HomeViewModel(repository)
        runCurrent()

        assertEquals(HomeUiState.Error, viewModel.uiState.value)
        viewModel.retry()
        runCurrent()

        assertEquals(2, attempts)
        assertEquals(HomeUiState.Content(listOf(food)), viewModel.uiState.value)
    }

    @Test
    fun cancelledLoadCannotReplaceNewerResultWhenRepositoryReturnsLate() = runTest {
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        val oldFood = FoodSummary(id = "old", name = "むかしのりんご")
        val newFood = FoodSummary(id = "new", name = "あたらしいりんご")
        val oldResult = CompletableDeferred<List<FoodSummary>>()
        val newResult = CompletableDeferred<List<FoodSummary>>()
        var attempts = 0
        val repository = FakeFoodRepository {
            attempts++
            if (attempts == 1) {
                withContext(NonCancellable) { oldResult.await() }
            } else {
                newResult.await()
            }
        }
        val viewModel = HomeViewModel(repository)
        runCurrent()

        viewModel.retry()
        runCurrent()
        newResult.complete(listOf(newFood))
        runCurrent()
        oldResult.complete(listOf(oldFood))
        runCurrent()

        assertEquals(HomeUiState.Content(listOf(newFood)), viewModel.uiState.value)
    }

    @Test
    fun cancelledLoadCannotReplaceNewerResultWhenRepositoryFailsLate() = runTest {
        Dispatchers.setMain(StandardTestDispatcher(testScheduler))
        val newFood = FoodSummary(id = "new", name = "あたらしいりんご")
        val oldResult = CompletableDeferred<List<FoodSummary>>()
        val newResult = CompletableDeferred<List<FoodSummary>>()
        var attempts = 0
        val repository = FakeFoodRepository {
            attempts++
            if (attempts == 1) {
                withContext(NonCancellable) { oldResult.await() }
            } else {
                newResult.await()
            }
        }
        val viewModel = HomeViewModel(repository)
        runCurrent()

        viewModel.retry()
        runCurrent()
        newResult.complete(listOf(newFood))
        runCurrent()
        oldResult.completeExceptionally(IllegalStateException("late failure"))
        runCurrent()

        assertEquals(HomeUiState.Content(listOf(newFood)), viewModel.uiState.value)
    }

    private class FakeFoodRepository(
        private val load: suspend () -> List<FoodSummary>,
    ) : FoodRepository {
        override suspend fun getFoods(): List<FoodSummary> = load()
    }
}
