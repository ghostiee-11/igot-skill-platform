"""Deterministic official-statistics calculations ported from the legacy engine."""
import math
from typing import Any
class StatisticalInputError(ValueError):pass
def _result(operation,value,unit,formula,steps,**metadata):return {"operation":operation,"result":value,"unit":unit,"formula":formula,"steps":steps,"metadata":metadata}
def calculate(operation:str,inputs:dict[str,Any])->dict[str,Any]:
    fn=_OPERATIONS.get(operation)
    if not fn:raise StatisticalInputError(f"unknown operation: {operation}")
    return fn(**inputs)
def price_relative(current_price:float,base_price:float):
    if base_price<=0 or current_price<0:raise StatisticalInputError("base price must be positive and current price non-negative")
    value=round(current_price/base_price*100,4);return _result("price_relative",value,"percent","R = (P1 / P0) * 100",[f"{current_price} / {base_price} * 100 = {value}"],base_price=base_price,current_price=current_price)
def inflation_rate(current_index=None,previous_index=None,curr_cpi=None,prev_cpi=None,**_):
    current=current_index if current_index is not None else curr_cpi;previous=previous_index if previous_index is not None else prev_cpi
    if current is None or previous is None or previous<=0:raise StatisticalInputError("current and positive previous index are required")
    value=round((current-previous)/previous*100,4);return _result("inflation_rate",value,"percent","((It - It-1) / It-1) * 100",[f"({current} - {previous}) / {previous} * 100 = {value}"],current_index=current,previous_index=previous)
def weighted_mean(values:list[float],weights:list[float],operation="weighted_mean"):
    if not values or len(values)!=len(weights) or any(w<0 for w in weights) or sum(weights)<=0:raise StatisticalInputError("equal non-empty values and non-negative weights with positive sum are required")
    numerator,denominator=sum(v*w for v,w in zip(values,weights)),sum(weights);value=round(numerator/denominator,4)
    return _result(operation,value,"index_points","sum(w*x) / sum(w)",[f"{numerator} / {denominator} = {value}"],sum_weights=denominator,weighted_sum=numerator)
def weighted_price_relatives(relatives,weights):return weighted_mean(relatives,weights,"weighted_price_relatives")
def weighted_price_relatives_basket(rel_food,rel_housing,rel_fuel,w_food,w_housing,w_fuel):return weighted_price_relatives([rel_food,rel_housing,rel_fuel],[w_food,w_housing,w_fuel])
def _basket_index(operation,p0,p1,quantities):
    if not p0 or len(p0)!=len(p1) or len(p0)!=len(quantities) or any(v<0 for v in [*p0,*p1,*quantities]):raise StatisticalInputError("price and quantity lists must have equal non-zero lengths and non-negative values")
    numerator,denominator=sum(p*q for p,q in zip(p1,quantities)),sum(p*q for p,q in zip(p0,quantities))
    if denominator<=0:raise StatisticalInputError("base expenditure must be positive")
    value=round(numerator/denominator*100,4);return _result(operation,value,"index_points","sum(p1*q) / sum(p0*q) * 100",[f"{numerator} / {denominator} * 100 = {value}"],numerator=numerator,denominator=denominator)
def laspeyres_index(base_prices,current_prices,base_quantities):return _basket_index("laspeyres_index",base_prices,current_prices,base_quantities)
def paasche_index(base_prices,current_prices,current_quantities):return _basket_index("paasche_index",base_prices,current_prices,current_quantities)
def laspeyres_index_basket(p0_a,p0_b,p1_a,p1_b,q0_a,q0_b):return laspeyres_index([p0_a,p0_b],[p1_a,p1_b],[q0_a,q0_b])
def fisher_index(laspeyres,paasche):
    if laspeyres<0 or paasche<0:raise StatisticalInputError("indices cannot be negative")
    value=round(math.sqrt(laspeyres*paasche),4);return _result("fisher_index",value,"index_points","sqrt(IL * IP)",[f"sqrt({laspeyres} * {paasche}) = {value}"],laspeyres=laspeyres,paasche=paasche)
def real_value(nominal_value=None,price_index=None,nominal_wage=None,cpi_index=None,**_):
    nominal=nominal_value if nominal_value is not None else nominal_wage;index=price_index if price_index is not None else cpi_index
    if nominal is None or index is None or index<=0:raise StatisticalInputError("nominal value and positive price index are required")
    value=round(nominal/index*100,2);return _result("real_value",value,"deflated_currency","nominal / index * 100",[f"{nominal} / {index} * 100 = {value}"],nominal_value=nominal,price_index=index)
_OPERATIONS={"price_relative":price_relative,"inflation_rate":inflation_rate,"weighted_mean":weighted_mean,"weighted_price_relatives":weighted_price_relatives,"weighted_price_relatives_basket":weighted_price_relatives_basket,"laspeyres_index":laspeyres_index,"laspeyres_index_basket":laspeyres_index_basket,"paasche_index":paasche_index,"fisher_index":fisher_index,"real_value":real_value}
def chart_spec(chart_type,title,data,x_field,y_fields):
    if chart_type not in {"line","bar","area","scatter"}:raise StatisticalInputError("unsupported chart type")
    if not data or not x_field or not y_fields:raise StatisticalInputError("chart data, x field and y fields are required")
    return {"type":chart_type,"title":title,"data":data,"x_axis":{"field":x_field,"label":x_field},"y_axis":{"fields":y_fields,"label":", ".join(y_fields)},"options":{"responsive":True,"accessible":True}}
