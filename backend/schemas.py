from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class KPIItem(BaseModel):
    value: float = Field(..., description="Numerical value of the metric")
    previous_value: float = Field(..., description="Previous equivalent period value")
    change_percentage: float = Field(..., description="Percentage change (+/-)")
    is_positive: bool = Field(..., description="Whether change is favorable")
    formatted_value: str = Field(..., description="Display string with formatting")
    formatted_change: str = Field(..., description="Display string with +/- percentage")


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
    growth_rate: Optional[float] = 0.0


class CategoryContribution(BaseModel):
    category_id: int
    category_name: str
    orders_count: int
    units_sold: int
    gross_revenue: float
    discount_amount: float
    refund_amount: float
    revenue: float
    profit: float
    percentage: float
    profit_margin: float


class RegionalPerformance(BaseModel):
    region_id: int
    region_name: str
    country: str
    state: Optional[str] = ""
    city: Optional[str] = ""
    code: str
    orders_count: int
    gross_revenue: float
    discount_amount: float
    refund_amount: float
    revenue: float
    profit: float
    profit_margin: float
    refund_rate: float
    discount_rate: float


class ProductPerformanceItem(BaseModel):
    product_id: int
    sku: str
    name: str
    category_name: str
    unit_price: float
    unit_cost: float
    units_sold: int
    gross_revenue: float
    discount_amount: float
    revenue: float
    refund_amount: float
    profit: float
    profit_margin: float
    discount_rate: float
    refund_rate: float
    rank: int


class CustomerSegmentStats(BaseModel):
    segment: str
    customers_count: int
    orders_count: int
    revenue: float
    profit: float
    refund_amount: float
    average_order_value: float
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
    discount_code: Optional[str] = "STANDARD"
    orders_count: int
    avg_discount_pct: float
    total_discount: float
    revenue_before: float
    revenue_after: float
    profit_impact: float


class RefundReasonItem(BaseModel):
    reason: str
    count: int
    total_amount: float
    avg_amount: float
    percentage: float


class BusinessInsightItem(BaseModel):
    id: str
    type: str # success, danger, warning, info
    title: str
    description: str
    metric_value: Optional[str] = None
    recommendation: Optional[str] = None
    category: str # Revenue, Discount, Refund, Profit, Product, Customer


class DataQualityReport(BaseModel):
    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    missing_columns: List[str]
    missing_values: Dict[str, int]
    column_types: Dict[str, str]
    quality_score: float
    preview: List[Dict[str, Any]]


class FilterOptions(BaseModel):
    categories: List[Dict[str, Any]]
    regions: List[Dict[str, Any]]
    segments: List[str]
    payment_methods: List[str]
    min_date: str
    max_date: str


class SalesSummary(BaseModel):
    total_orders: int
    total_units_sold: int
    total_sales: float
    average_order_value: float


class PaymentMethodStats(BaseModel):
    payment_method: str
    name: str
    orders_count: int
    count: int
    total_amount: float
    revenue: float
    value: float
    avg_amount: float
    percentage: float


class DiscountSummary(BaseModel):
    total_discounts: float
    total_instances: int
    average_discount_percentage: float
    revenue_erosion_rate: float


class RefundSummary(BaseModel):
    total_refund_amount: float
    total_refunds_count: int
    refunded_orders_count: int
    refund_rate: float


class ProfitabilitySummary(BaseModel):
    gross_revenue: float
    discounts: float
    refunds: float
    net_revenue: float
    cost_of_goods_sold: float
    gross_profit: float
    profit_margin: float


class ProductQuadrantItem(BaseModel):
    product_id: int
    sku: str
    name: str
    category_name: str
    unit_price: float
    unit_cost: float
    units_sold: int
    gross_revenue: float
    discount_amount: float
    revenue: float
    refund_amount: float
    profit: float
    profit_margin: float
    discount_rate: float
    refund_rate: float
    rank: int
    classification: str
    is_high_revenue: bool
    is_high_margin: bool


class CustomerSummary(BaseModel):
    total_customers: int
    active_orders: int
    total_revenue: float
    average_customer_spending: float


class TopCustomerItem(BaseModel):
    id: int
    customer_code: str
    name: str
    segment: str
    email: str
    region_name: str
    total_orders: int
    total_spent: float
    refund_total: float


class RevenueSummary(BaseModel):
    gross_revenue: KPIItem
    net_revenue: KPIItem
    discounts: KPIItem
    refunds: KPIItem
    growth_rate: float


class ExecutiveReport(BaseModel):
    kpis: Dict[str, Any]
    categories: List[CategoryContribution]
    regions: List[RegionalPerformance]
    trends: List[TrendDataPoint]
    generated_at: str


class UploadHistoryItem(BaseModel):
    id: int
    filename: str
    rows_count: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    status: str
    upload_date: str
    summary_notes: Optional[str] = None


class CategoryDiscountImpact(BaseModel):
    category_name: str
    gross_revenue: float
    discount_amount: float
    discount_percentage: float


class CategoryRefundImpact(BaseModel):
    category_name: str
    refund_count: int
    refund_amount: float
    category_revenue: float
    refund_rate: float


class HighRefundProductItem(BaseModel):
    product_id: int
    sku: str
    product_name: str
    category_name: str
    refund_claims: int
    total_refunded: float
    gross_sales: float
    refund_rate: float


class PowerBiDatasetRow(BaseModel):
    order_number: str
    order_date: str
    customer_code: str
    customer_name: str
    customer_segment: str
    region_name: str
    country: str
    product_sku: str
    product_name: str
    category_name: str
    quantity: int
    unit_price: float
    unit_cost: float
    gross_revenue: float
    discount_amount: float
    net_revenue: float
    cogs: float
    profit: float
    refund_amount: float
    payment_method: str
    status: str

