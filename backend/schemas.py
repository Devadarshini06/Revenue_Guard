from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class KPIItem(BaseModel):
    value: float
    previous_value: float
    change_percentage: float
    is_positive: bool
    formatted_value: str
    formatted_change: str

class DashboardKPIs(BaseModel):
    total_revenue: KPIItem
    net_revenue: KPIItem
    total_orders: KPIItem
    average_order_value: KPIItem
    total_discounts: KPIItem
    total_refunds: KPIItem
    gross_profit: KPIItem
    profit_margin: KPIItem

class TrendDataPoint(BaseModel):
    date: str
    label: str
    gross_revenue: float
    net_revenue: float
    total_revenue: float
    profit: float
    orders_count: int
    discounts: float
    refunds: float

class CategoryContribution(BaseModel):
    category_id: int
    category_name: str
    revenue: float
    profit: float
    orders_count: int
    units_sold: int
    percentage: float
    profit_margin: float

class RegionalPerformance(BaseModel):
    region_id: int
    region_name: str
    country: str
    state: Optional[str] = None
    city: Optional[str] = None
    code: str
    revenue: float
    profit: float
    orders_count: int
    refund_amount: float
    refund_rate: float
    discount_amount: float
    discount_rate: float
    profit_margin: float

class ProductPerformanceItem(BaseModel):
    product_id: int
    sku: str
    name: str
    category_name: str
    unit_price: float
    unit_cost: float
    revenue: float
    units_sold: int
    profit: float
    profit_margin: float
    discount_amount: float
    discount_rate: float
    refund_amount: float
    refund_rate: float
    rank: int

class CustomerSegmentStats(BaseModel):
    segment: str
    customers_count: int
    revenue: float
    orders_count: int
    average_order_value: float
    profit: float
    refund_amount: float
    repeat_rate: float

class RecentTransactionItem(BaseModel):
    order_id: int
    order_number: str
    order_date: str
    customer_name: str
    customer_segment: str
    product_summary: str
    gross_revenue: float
    discount_amount: float
    refund_amount: float
    net_amount: float
    status: str
    payment_method: str

class DiscountImpactItem(BaseModel):
    discount_type: str
    discount_code: Optional[str]
    total_discount: float
    orders_count: int
    avg_discount_pct: float
    revenue_before: float
    revenue_after: float
    profit_impact: float

class RefundReasonItem(BaseModel):
    reason: str
    count: int
    total_amount: float
    percentage: float
    avg_amount: float

class BusinessInsightItem(BaseModel):
    id: str
    type: str # success, danger, warning, info
    title: str
    description: str
    metric_value: Optional[str] = None
    recommendation: Optional[str] = None
    category: str # Revenue, Discount, Refund, Profit, Product, Customer

class DataQualityReport(BaseModel):
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    missing_values: Dict[str, int]
    column_types: Dict[str, str]
    quality_score: float

class FilterOptions(BaseModel):
    categories: List[Dict[str, Any]]
    regions: List[Dict[str, Any]]
    segments: List[str]
    payment_methods: List[str]
    min_date: str
    max_date: str

