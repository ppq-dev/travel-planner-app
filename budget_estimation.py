import json
import os
import re
from typing import Dict, List, Any, Optional

import requests
from bs4 import BeautifulSoup

from utils.llm_utils import call_llm


class BudgetEstimator:
    """
    A class to estimate the budget for a travel plan.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the BudgetEstimator.

        Args:
            api_key: Optional API key for external services.
        """
        self.api_key = api_key

    def estimate_budget(self, travel_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate the budget for a given travel plan.

        Args:
            travel_plan: A dictionary containing the travel plan details.

        Returns:
            A dictionary containing the estimated budget breakdown.
        """
        # Extract relevant information from the travel plan
        destination = travel_plan.get("destination", "")
        duration = travel_plan.get("duration", 0)
        activities = travel_plan.get("activities", [])
        accommodation = travel_plan.get("accommodation", {})
        transportation = travel_plan.get("transportation", {})

        # Initialize budget breakdown
        budget_breakdown = {
            "accommodation": 0,
            "transportation": 0,
            "activities": 0,
            "food": 0,
            "miscellaneous": 0,
            "total": 0
        }

        # Estimate accommodation costs
        budget_breakdown["accommodation"] = self._estimate_accommodation_cost(accommodation, duration)

        # Estimate transportation costs
        budget_breakdown["transportation"] = self._estimate_transportation_cost(transportation)

        # Estimate activity costs
        budget_breakdown["activities"] = self._estimate_activity_cost(activities)

        # Estimate food costs
        budget_breakdown["food"] = self._estimate_food_cost(destination, duration)

        # Estimate miscellaneous costs
        budget_breakdown["miscellaneous"] = self._estimate_miscellaneous_cost(destination, duration)

        # Calculate total budget
        budget_breakdown["total"] = sum([
            budget_breakdown["accommodation"],
            budget_breakdown["transportation"],
            budget_breakdown["activities"],
            budget_breakdown["food"],
            budget_breakdown["miscellaneous"]
        ])

        return budget_breakdown

    def _estimate_accommodation_cost(self, accommodation: Dict[str, Any], duration: int) -> float:
        """
        Estimate accommodation cost.

        Args:
            accommodation: Accommodation details.
            duration: Duration of stay in nights.

        Returns:
            Estimated accommodation cost.
        """
        if not accommodation:
            return 0.0

        accommodation_type = accommodation.get("type", "hotel").lower()
        quality = accommodation.get("quality", "medium").lower()

        # Average nightly rates by accommodation type and quality
        rates = {
            "hotel": {"budget": 50, "medium": 100, "luxury": 200},
            "hostel": {"budget": 20, "medium": 30, "luxury": 50},
            "apartment": {"budget": 70, "medium": 120, "luxury": 250},
            "vacation_rental": {"budget": 80, "medium": 150, "luxury": 300},
            "resort": {"budget": 100, "medium": 200, "luxury": 400}
        }

        default_rate = rates.get("hotel", {"medium": 100})
        rate = rates.get(accommodation_type, default_rate).get(quality, 100)

        return rate * duration

    def _estimate_transportation_cost(self, transportation: Dict[str, Any]) -> float:
        """
        Estimate transportation cost.

        Args:
            transportation: Transportation details.

        Returns:
            Estimated transportation cost.
        """
        if not transportation:
            return 0.0

        transportation_type = transportation.get("type", "flight").lower()
        distance = transportation.get("distance", 0)
        quality = transportation.get("quality", "economy").lower()

        # Cost per mile/km by transportation type and quality
        rates = {
            "flight": {"economy": 0.15, "business": 0.30, "first": 0.50},
            "train": {"economy": 0.10, "business": 0.20, "first": 0.30},
            "bus": {"economy": 0.05, "business": 0.08, "first": 0.12},
            "car": {"economy": 0.25, "business": 0.35, "first": 0.50}  # per mile including rental and gas
        }

        default_rate = rates.get("flight", {"economy": 0.15})
        rate = rates.get(transportation_type, default_rate).get(quality, 0.15)

        return rate * distance

    def _estimate_activity_cost(self, activities: List[Dict[str, Any]]) -> float:
        """
        Estimate activity costs.

        Args:
            activities: List of activity details.

        Returns:
            Estimated activity cost.
        """
        if not activities:
            return 0.0

        total_cost = 0.0

        for activity in activities:
            activity_type = activity.get("type", "sightseeing").lower()
            duration = activity.get("duration", 2)  # hours
            quality = activity.get("quality", "standard").lower()

            # Average cost by activity type and quality
            rates = {
                "sightseeing": {"free": 0, "standard": 15, "premium": 30},
                "museum": {"free": 0, "standard": 20, "premium": 40},
                "adventure": {"standard": 50, "premium": 100},
                "cultural": {"standard": 25, "premium": 50},
                "entertainment": {"standard": 30, "premium": 60},
                "shopping": {"standard": 50, "premium": 100},
                "dining": {"standard": 40, "premium": 80}
            }

            default_rate = rates.get("sightseeing", {"standard": 15})
            rate = rates.get(activity_type, default_rate).get(quality, 15)

            total_cost += rate

        return total_cost

    def _estimate_food_cost(self, destination: str, duration: int) -> float:
        """
        Estimate food costs.

        Args:
            destination: Travel destination.
            duration: Duration of stay in days.

        Returns:
            Estimated food cost.
        """
        # Average daily food cost by destination type (simplified)
        # In a real implementation, this would use location-specific data
        destination_factor = 1.0
        
        if any(word in destination.lower() for word in ["europe", "usa", "canada", "australia"]):
            destination_factor = 1.5
        elif any(word in destination.lower() for word in ["asia", "south america", "africa"]):
            destination_factor = 0.7

        # Average daily food cost: $40 * destination factor
        daily_food_cost = 40 * destination_factor
        
        return daily_food_cost * duration

    def _estimate_miscellaneous_cost(self, destination: str, duration: int) -> float:
        """
        Estimate miscellaneous costs.

        Args:
            destination: Travel destination.
            duration: Duration of stay in days.

        Returns:
            Estimated miscellaneous cost.
        """
        # Miscellaneous costs (souvenirs, tips, local transportation, etc.)
        # Average $20 per day
        return 20 * duration

    def refine_budget_with_llm(self, travel_plan: Dict[str, Any], initial_budget: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refine the budget estimation using LLM for more accurate results.

        Args:
            travel_plan: The travel plan details.
            initial_budget: The initial budget estimation.

        Returns:
            Refined budget estimation.
        """
        prompt = f"""
        Given the following travel plan:
        {json.dumps(travel_plan, indent=2)}

        And the initial budget estimation:
        {json.dumps(initial_budget, indent=2)}

        Please provide a more accurate budget estimation considering:
        1. Current market prices for the destination
        2. Seasonal variations
        3. Specific accommodation and transportation details
        4. Activity costs
        5. Food and miscellaneous expenses

        Return the refined budget in the same JSON format.
        """

        try:
            refined_budget = call_llm(prompt)
            return json.loads(refined_budget)
        except Exception as e:
            print(f"Error refining budget with LLM: {e}")
            return initial_budget

    def scrape_prices(self, destination: str, accommodation_type: str) -> Dict[str, float]:
        """
        Scrape current prices for accommodation in a destination.
        
        Args:
            destination: The travel destination.
            accommodation_type: Type of accommodation.
            
        Returns:
            Dictionary with price information.
        """
        # This is a placeholder for actual web scraping logic
        # In a real implementation, this would scrape booking sites
        
        prices = {
            "budget": 60,
            "medium": 120,
            "luxury": 250
        }
        
        return prices


def main():
    """Example usage of the BudgetEstimator."""
    
    # Example travel plan
    travel_plan = {
        "destination": "Paris, France",
        "duration": 7,
        "accommodation": {
            "type": "hotel",
            "quality": "medium"
        },
        "transportation": {
            "type": "flight",
            "distance": 3600,  # miles from NYC to Paris
            "quality": "economy"
        },
        "activities": [
            {"type": "museum", "quality": "standard"},
            {"type": "sightseeing", "quality": "standard"},
            {"type": "dining", "quality": "premium"}
        ]
    }

    estimator = BudgetEstimator()
    budget = estimator.estimate_budget(travel_plan)
    
    print("Budget Estimation:")
    print(json.dumps(budget, indent=2))


if __name__ == "__main__":
    main()