"""
Shipping Tool
Checks shipping eligibility and estimates
"""

from typing import Dict, Any
from core.tools.base import Tool


class ShippingTool(Tool):
    """Check shipping eligibility and delivery estimates"""
    
    def __init__(self, brand_name: str = "fashionhub"):
        """
        Initialize shipping tool
        
        Args:
            brand_name: Brand name
        """
        super().__init__(
            name="check_shipping_eligibility",
            description="Check if shipping is available to a location and get delivery estimate"
        )
        
        # Serviceable pincodes (simplified - in production, load from database)
        self.serviceable_areas = {
            # Major cities
            "110001": {"city": "Delhi", "days": "2-3", "cod": True},
            "400001": {"city": "Mumbai", "days": "2-3", "cod": True},
            "560001": {"city": "Bangalore", "days": "2-3", "cod": True},
            "600001": {"city": "Chennai", "days": "3-4", "cod": True},
            "700001": {"city": "Kolkata", "days": "3-4", "cod": True},
            "500001": {"city": "Hyderabad", "days": "3-4", "cod": True},
            
            # Tier 2 cities (examples)
            "302001": {"city": "Jaipur", "days": "3-5", "cod": True},
            "380001": {"city": "Ahmedabad", "days": "3-5", "cod": True},
            "411001": {"city": "Pune", "days": "2-4", "cod": True},
        }
        
        # Free shipping threshold
        self.free_shipping_threshold = 1500  # ₹1500
    
    def validate_params(self, **kwargs) -> tuple[bool, str]:
        """Validate pincode parameter"""
        pincode = kwargs.get("pincode")
        
        if not pincode:
            return False, "pincode is required"
        
        # Validate pincode format (6 digits)
        if not str(pincode).isdigit() or len(str(pincode)) != 6:
            return False, "pincode must be 6 digits"
        
        return True, None
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Check shipping eligibility
        
        Args:
            pincode: Delivery pincode
            order_value: Order value for shipping calculation (optional)
        
        Returns:
            Shipping details or error
        """
        # Validate
        is_valid, error = self.validate_params(**kwargs)
        if not is_valid:
            return self.format_result(False, error=error)
        
        pincode = str(kwargs["pincode"])
        order_value = kwargs.get("order_value", 0)
        
        try:
            # Check if serviceable
            if pincode in self.serviceable_areas:
                area_info = self.serviceable_areas[pincode]
                
                # Calculate shipping
                shipping_cost = 0
                if order_value < self.free_shipping_threshold:
                    shipping_cost = 100  # ₹100 standard shipping
                
                result_data = {
                    "serviceable": True,
                    "city": area_info["city"],
                    "delivery_days": area_info["days"],
                    "cod_available": area_info["cod"],
                    "shipping_cost": shipping_cost,
                    "free_shipping": order_value >= self.free_shipping_threshold,
                    "free_shipping_threshold": self.free_shipping_threshold,
                    "order_value": order_value
                }
                
                return self.format_result(True, data=result_data)
            else:
                # Check first 3 digits for region
                region_code = pincode[:3]
                
                # Simplified regional check
                if region_code in ["110", "400", "560", "600", "700", "500"]:
                    # Likely serviceable but not in exact list
                    result_data = {
                        "serviceable": True,
                        "city": "Your area",
                        "delivery_days": "4-6",
                        "cod_available": True,
                        "shipping_cost": 100,
                        "free_shipping": order_value >= self.free_shipping_threshold,
                        "note": "Delivery time may vary for your specific location"
                    }
                    return self.format_result(True, data=result_data)
                else:
                    # Not serviceable
                    result_data = {
                        "serviceable": False,
                        "message": f"Sorry, we don't currently deliver to pincode {pincode}",
                        "alternative": "Please check our serviceable areas or contact support"
                    }
                    return self.format_result(True, data=result_data)
            
        except Exception as e:
            return self.format_result(
                False,
                error=f"Shipping check failed: {str(e)}"
            )


# Convenience function
def check_shipping_eligibility(pincode: str, order_value: float = 0) -> Dict:
    """
    Check shipping eligibility
    
    Args:
        pincode: Delivery pincode
        order_value: Order value
    
    Returns:
        Shipping details
    """
    tool = ShippingTool()
    return tool.execute(pincode=pincode, order_value=order_value)
