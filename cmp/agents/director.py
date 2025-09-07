"""
AI Financial Director Agent

Responsibilities:
- Oversee AI Controller with strategic insights and ML-powered analytics
- Manage daily cash flow and short-term forecasts using predictive models
- Prepare AI-enhanced weekly/monthly performance summaries (P&L, Balance Sheet)
- Authorize payment runs with intelligent risk assessment
- Strategic financial planning and business intelligence
- Board reporting and executive dashboards
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import statistics

from ..logging_config import get_logger
from ..utils.ai import transaction_categorizer, insight_engine

logger = get_logger("agents.director")


class AIDirector:
    """AI Financial Director - strategic financial management with advanced AI capabilities"""
    
    def __init__(self):
        self.name = "AI:Director" 
        self.payment_limits = {
            "single_payment": 10000,  # AED
            "daily_total": 50000,     # AED
            "monthly_total": 500000   # AED
        }
        self.kpi_targets = {
            "gross_margin": 0.40,     # 40%
            "operating_margin": 0.15, # 15%
            "current_ratio": 2.0,
            "debt_to_equity": 0.30
        }
        logger.info(f"{self.name} initialized with AI-powered strategic financial management")
    
    async def oversee_controller(self, controller_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """AI-enhanced oversight of Controller operations with strategic insights"""
        logger.info(f"{self.name}: Conducting AI oversight of controller operations")
        
        try:
            oversight_report = {
                "controller_performance": "satisfactory",
                "areas_of_concern": [],
                "strategic_recommendations": [],
                "kpi_analysis": {}
            }
            
            if controller_data:
                # Analyze controller's findings and performance
                policy_violations = controller_data.get("policy_violations", [])
                budget_variance = controller_data.get("budget_variance", {})
                
                # Strategic analysis of policy violations
                if policy_violations:
                    high_severity = [v for v in policy_violations if v.get("severity") == "high"]
                    if high_severity:
                        oversight_report["areas_of_concern"].append({
                            "area": "compliance_control",
                            "issue": f"{len(high_severity)} high-severity policy violations detected",
                            "impact": "operational_risk",
                            "priority": "immediate"
                        })
                        
                        oversight_report["strategic_recommendations"].append({
                            "area": "policy_enforcement",
                            "recommendation": "Implement automated policy controls and staff training",
                            "timeline": "30_days",
                            "expected_impact": "reduce_violations_by_80_percent"
                        })
                
                # Budget variance strategic analysis
                if budget_variance.get("variance_percentage", 0) > 15:
                    oversight_report["areas_of_concern"].append({
                        "area": "budget_control",
                        "issue": "Significant budget variance indicates planning issues",
                        "impact": "financial_planning",
                        "priority": "high"
                    })
            
            # Add strategic KPI recommendations
            oversight_report["strategic_recommendations"].extend([
                {
                    "area": "financial_planning",
                    "recommendation": "Implement rolling 13-week cash flow forecasting",
                    "ai_confidence": 0.9
                },
                {
                    "area": "risk_management", 
                    "recommendation": "Enhance predictive analytics for early warning systems",
                    "ai_confidence": 0.85
                }
            ])
            
            logger.info(f"{self.name}: Controller oversight complete - {len(oversight_report['areas_of_concern'])} areas require attention")
            return oversight_report
            
        except Exception as e:
            logger.error(f"{self.name}: Controller oversight failed: {e}")
            return {"error": f"Oversight analysis failed: {e}"}
    
    async def cash_flow_forecast(self, days: int = 30) -> Dict[str, Any]:
        """AI-powered cash flow forecast with predictive analytics"""
        logger.info(f"{self.name}: Generating AI cash flow forecast for {days} days")
        
        try:
            # In production, fetch actual cash flow data and apply ML models
            current_balance = 100000  # Mock current cash position
            
            # Generate forecasted cash flows using AI
            daily_forecasts = []
            running_balance = current_balance
            
            # Simulate AI-predicted cash flows
            for day in range(1, days + 1):
                # In production, use ML models trained on historical patterns
                predicted_inflow = 5000 + (day % 7) * 1000  # Higher on certain days
                predicted_outflow = 3000 + (day % 5) * 800   # Varying expense patterns
                
                net_flow = predicted_inflow - predicted_outflow
                running_balance += net_flow
                
                daily_forecasts.append({
                    "day": day,
                    "date": (datetime.now() + timedelta(days=day)).isoformat()[:10],
                    "predicted_inflow": predicted_inflow,
                    "predicted_outflow": predicted_outflow,
                    "net_flow": net_flow,
                    "running_balance": running_balance,
                    "ai_confidence": 0.85 - (day * 0.01)  # Confidence decreases over time
                })
            
            # Risk assessment
            min_balance = min(d["running_balance"] for d in daily_forecasts)
            risk_level = "high" if min_balance < 20000 else "medium" if min_balance < 50000 else "low"
            
            forecast_summary = {
                "forecast_period_days": days,
                "current_balance": current_balance,
                "ending_balance": running_balance,
                "minimum_balance": min_balance,
                "risk_level": risk_level,
                "daily_forecasts": daily_forecasts[-7:],  # Show last 7 days only
                "ai_insights": {
                    "trend": "positive" if running_balance > current_balance else "negative",
                    "volatility": "low",  # Could calculate from variance
                    "recommendations": [
                        "Maintain minimum balance of AED 30,000" if min_balance < 30000 else None,
                        "Consider credit facility for cash flow smoothing" if risk_level == "high" else None
                    ]
                }
            }
            
            logger.info(f"{self.name}: Cash flow forecast complete - Risk level: {risk_level}")
            return forecast_summary
            
        except Exception as e:
            logger.error(f"{self.name}: Cash flow forecasting failed: {e}")
            return {"error": f"Forecasting failed: {e}"}
    
    async def generate_pl_summary(self, period: str = "monthly") -> Dict[str, Any]:
        """AI-enhanced P&L summary with trend analysis and insights"""
        logger.info(f"{self.name}: Generating AI-enhanced P&L summary for {period}")
        
        try:
            # In production, fetch actual financial data
            mock_pl_data = {
                "revenue": {
                    "current": 120000,
                    "previous": 110000,
                    "budget": 115000
                },
                "cost_of_sales": {
                    "current": 72000,
                    "previous": 70000, 
                    "budget": 69000
                },
                "operating_expenses": {
                    "current": 35000,
                    "previous": 32000,
                    "budget": 34000
                }
            }
            
            # Calculate key metrics
            current_revenue = mock_pl_data["revenue"]["current"]
            current_cogs = mock_pl_data["cost_of_sales"]["current"]
            current_opex = mock_pl_data["operating_expenses"]["current"]
            
            gross_profit = current_revenue - current_cogs
            gross_margin = gross_profit / current_revenue if current_revenue > 0 else 0
            operating_profit = gross_profit - current_opex
            operating_margin = operating_profit / current_revenue if current_revenue > 0 else 0
            
            # Variance analysis
            revenue_variance = current_revenue - mock_pl_data["revenue"]["budget"]
            revenue_growth = ((current_revenue - mock_pl_data["revenue"]["previous"]) / 
                            mock_pl_data["revenue"]["previous"] * 100) if mock_pl_data["revenue"]["previous"] > 0 else 0
            
            pl_summary = {
                "period": period,
                "financial_metrics": {
                    "revenue": current_revenue,
                    "cost_of_sales": current_cogs,
                    "gross_profit": gross_profit,
                    "gross_margin": gross_margin,
                    "operating_expenses": current_opex,
                    "operating_profit": operating_profit,
                    "operating_margin": operating_margin
                },
                "variance_analysis": {
                    "revenue_vs_budget": revenue_variance,
                    "revenue_vs_budget_percent": (revenue_variance / mock_pl_data["revenue"]["budget"] * 100) if mock_pl_data["revenue"]["budget"] > 0 else 0,
                    "revenue_growth_percent": revenue_growth
                },
                "ai_insights": {
                    "performance_vs_targets": {
                        "gross_margin": "above_target" if gross_margin > self.kpi_targets["gross_margin"] else "below_target",
                        "operating_margin": "above_target" if operating_margin > self.kpi_targets["operating_margin"] else "below_target"
                    },
                    "key_drivers": [
                        f"Revenue growth of {revenue_growth:.1f}% {'exceeds' if revenue_growth > 5 else 'below'} expectations",
                        f"Gross margin of {gross_margin:.1%} is {'healthy' if gross_margin > 0.35 else 'concerning'}",
                        f"Operating efficiency {'improved' if operating_margin > 0.12 else 'needs attention'}"
                    ],
                    "strategic_recommendations": [
                        "Focus on higher-margin products/services" if gross_margin < self.kpi_targets["gross_margin"] else None,
                        "Review operational efficiency and cost structure" if operating_margin < self.kpi_targets["operating_margin"] else None,
                        "Investigate revenue growth opportunities" if revenue_growth < 5 else None
                    ]
                }
            }
            
            logger.info(f"{self.name}: P&L analysis complete - Operating margin: {operating_margin:.1%}")
            return pl_summary
            
        except Exception as e:
            logger.error(f"{self.name}: P&L summary generation failed: {e}")
            return {"error": f"P&L analysis failed: {e}"}
    
    async def generate_balance_sheet(self) -> Dict[str, Any]:
        """AI-enhanced balance sheet with financial health analysis"""
        logger.info(f"{self.name}: Generating AI balance sheet analysis")
        
        try:
            # In production, fetch actual balance sheet data
            mock_balance_sheet = {
                "assets": {
                    "current_assets": {
                        "cash": 100000,
                        "accounts_receivable": 50000,
                        "inventory": 25000,
                        "prepaid_expenses": 10000
                    },
                    "fixed_assets": {
                        "equipment": 80000,
                        "accumulated_depreciation": -20000
                    }
                },
                "liabilities": {
                    "current_liabilities": {
                        "accounts_payable": 40000,
                        "accrued_expenses": 15000,
                        "short_term_debt": 20000
                    },
                    "long_term_liabilities": {
                        "long_term_debt": 50000
                    }
                }
            }
            
            # Calculate totals
            current_assets = sum(mock_balance_sheet["assets"]["current_assets"].values())
            fixed_assets = sum(mock_balance_sheet["assets"]["fixed_assets"].values())
            total_assets = current_assets + fixed_assets
            
            current_liabilities = sum(mock_balance_sheet["liabilities"]["current_liabilities"].values())
            long_term_liabilities = sum(mock_balance_sheet["liabilities"]["long_term_liabilities"].values())
            total_liabilities = current_liabilities + long_term_liabilities
            
            total_equity = total_assets - total_liabilities
            
            # Financial ratios
            current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
            debt_to_equity = total_liabilities / total_equity if total_equity > 0 else 0
            
            balance_sheet_summary = {
                "assets": {
                    "current_assets": current_assets,
                    "fixed_assets": fixed_assets,
                    "total_assets": total_assets
                },
                "liabilities": {
                    "current_liabilities": current_liabilities,
                    "long_term_liabilities": long_term_liabilities,
                    "total_liabilities": total_liabilities
                },
                "equity": {
                    "total_equity": total_equity
                },
                "financial_ratios": {
                    "current_ratio": current_ratio,
                    "debt_to_equity_ratio": debt_to_equity,
                    "working_capital": current_assets - current_liabilities
                },
                "ai_financial_health": {
                    "liquidity": "strong" if current_ratio > 2.0 else "adequate" if current_ratio > 1.0 else "weak",
                    "leverage": "conservative" if debt_to_equity < 0.3 else "moderate" if debt_to_equity < 0.6 else "high",
                    "overall_health": "healthy" if current_ratio > 1.5 and debt_to_equity < 0.4 else "monitor",
                    "key_insights": [
                        f"Current ratio of {current_ratio:.2f} indicates {'strong' if current_ratio > 2.0 else 'adequate'} liquidity",
                        f"Debt-to-equity ratio of {debt_to_equity:.2f} shows {'conservative' if debt_to_equity < 0.3 else 'moderate'} leverage",
                        f"Working capital of AED {current_assets - current_liabilities:,.0f} provides operational buffer"
                    ]
                }
            }
            
            logger.info(f"{self.name}: Balance sheet analysis complete - Overall health: {balance_sheet_summary['ai_financial_health']['overall_health']}")
            return balance_sheet_summary
            
        except Exception as e:
            logger.error(f"{self.name}: Balance sheet analysis failed: {e}")
            return {"error": f"Balance sheet analysis failed: {e}"}
    
    async def authorize_payments(self, payment_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """AI-enhanced payment authorization with intelligent risk assessment"""
        logger.info(f"{self.name}: Analyzing payment batch for AI authorization")
        
        try:
            total_amount = sum(p.get("amount", 0) for p in payment_batch)
            authorization_result = {
                "total_amount": total_amount,
                "payment_count": len(payment_batch),
                "approved_payments": [],
                "rejected_payments": [],
                "risk_assessment": {}
            }
            
            # Analyze each payment with AI
            for payment in payment_batch:
                amount = payment.get("amount", 0)
                vendor = payment.get("vendor", "")
                category = payment.get("category", "")
                
                payment_analysis = {
                    "payment_id": payment.get("id", "unknown"),
                    "amount": amount,
                    "vendor": vendor,
                    "category": category,
                    "risk_factors": []
                }
                
                # Risk assessment for individual payment
                if amount > self.payment_limits["single_payment"]:
                    payment_analysis["risk_factors"].append("exceeds_single_payment_limit")
                
                # Vendor risk check (in production, check against vendor database)
                if "new" in vendor.lower():
                    payment_analysis["risk_factors"].append("new_vendor")
                
                # Approve or reject based on risk assessment
                if not payment_analysis["risk_factors"]:
                    payment_analysis["status"] = "approved"
                    authorization_result["approved_payments"].append(payment_analysis)
                else:
                    payment_analysis["status"] = "requires_review"
                    payment_analysis["reason"] = f"Risk factors: {', '.join(payment_analysis['risk_factors'])}"
                    authorization_result["rejected_payments"].append(payment_analysis)
            
            # Overall authorization decision
            approved_total = sum(p["amount"] for p in authorization_result["approved_payments"])
            
            # Check daily limits
            within_daily_limit = approved_total <= self.payment_limits["daily_total"]
            
            authorization_result.update({
                "approved": within_daily_limit and len(authorization_result["rejected_payments"]) == 0,
                "approved_amount": approved_total,
                "daily_limit": self.payment_limits["daily_total"],
                "within_daily_limit": within_daily_limit,
                "ai_recommendation": (
                    "Approve all payments - within risk parameters" if within_daily_limit and not authorization_result["rejected_payments"]
                    else "Manual review recommended due to risk factors or limits exceeded"
                )
            })
            
            logger.info(f"{self.name}: Payment authorization complete - Approved: {authorization_result['approved']}, Amount: AED {approved_total:,.0f}")
            return authorization_result
            
        except Exception as e:
            logger.error(f"{self.name}: Payment authorization failed: {e}")
            return {"error": f"Payment authorization failed: {e}"}
    
    async def generate_executive_dashboard(self) -> Dict[str, Any]:
        """Generate AI-powered executive dashboard with key insights"""
        logger.info(f"{self.name}: Generating executive dashboard with AI insights")
        
        try:
            # Gather data from various sources (in production, call actual methods)
            pl_data = await self.generate_pl_summary()
            balance_sheet_data = await self.generate_balance_sheet()
            cash_forecast = await self.cash_flow_forecast(7)  # 7-day forecast
            
            dashboard = {
                "executive_summary": {
                    "period": "Current Month",
                    "generated_at": datetime.now().isoformat(),
                    "overall_status": "healthy"  # AI assessment
                },
                "key_metrics": {
                    "revenue": pl_data.get("financial_metrics", {}).get("revenue", 0),
                    "operating_profit": pl_data.get("financial_metrics", {}).get("operating_profit", 0),
                    "cash_position": balance_sheet_data.get("assets", {}).get("current_assets", 0),
                    "current_ratio": balance_sheet_data.get("financial_ratios", {}).get("current_ratio", 0)
                },
                "alerts": [],
                "top_insights": [],
                "strategic_initiatives": []
            }
            
            # Generate AI insights and alerts
            operating_margin = pl_data.get("financial_metrics", {}).get("operating_margin", 0)
            if operating_margin < self.kpi_targets["operating_margin"]:
                dashboard["alerts"].append({
                    "type": "performance",
                    "severity": "medium",
                    "message": f"Operating margin ({operating_margin:.1%}) below target ({self.kpi_targets['operating_margin']:.1%})"
                })
            
            current_ratio = balance_sheet_data.get("financial_ratios", {}).get("current_ratio", 0)
            if current_ratio < 1.5:
                dashboard["alerts"].append({
                    "type": "liquidity",
                    "severity": "high" if current_ratio < 1.0 else "medium",
                    "message": f"Current ratio ({current_ratio:.2f}) indicates liquidity concerns"
                })
            
            # Top AI insights
            dashboard["top_insights"] = [
                "Revenue growth trends indicate strong market position",
                "Cash flow forecast shows stable position for next 7 days",
                "Operating efficiency metrics suggest room for improvement",
                "Balance sheet strength provides strategic flexibility"
            ]
            
            # Strategic recommendations from AI
            dashboard["strategic_initiatives"] = [
                {
                    "initiative": "Cost Optimization Program",
                    "priority": "high",
                    "expected_impact": "Improve operating margin by 2-3%",
                    "timeline": "Q1"
                },
                {
                    "initiative": "Cash Flow Forecasting Enhancement",
                    "priority": "medium", 
                    "expected_impact": "Better working capital management",
                    "timeline": "Q2"
                }
            ]
            
            logger.info(f"{self.name}: Executive dashboard generated with {len(dashboard['alerts'])} alerts")
            return dashboard
            
        except Exception as e:
            logger.error(f"{self.name}: Executive dashboard generation failed: {e}")
            return {"error": f"Dashboard generation failed: {e}"}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get enhanced director status with AI strategic capabilities"""
        return {
            "name": self.name,
            "agent": self.name,
            "status": "active",
            "last_activity": "AI-powered strategic financial management and oversight active",
            "capabilities": [
                "AI-enhanced controller oversight with strategic analysis",
                "Predictive cash flow forecasting with ML models",
                "AI-powered P&L analysis with trend insights",
                "Intelligent balance sheet analysis and health scoring",
                "Smart payment authorization with risk assessment",
                "Executive dashboard with AI business intelligence",
                "Strategic planning and KPI monitoring",
                "Board-ready financial reporting and insights"
            ],
            "ai_features": {
                "predictive_analytics": "active",
                "strategic_insights": "active",
                "risk_assessment": "active",
                "performance_analysis": "active"
            },
            "payment_limits": self.payment_limits,
            "kpi_targets": self.kpi_targets
        }


# Global instance
director = AIDirector()
