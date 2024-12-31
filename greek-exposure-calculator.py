import robin_stocks as rs
import os
import pandas as pd
import matplotlib.pyplot as plt

rh_user = os.environ.get("rh_username")
rh_pass = os.environ.get("rh_password")

rs.robinhood.authentication.login(username=rh_user, password=rh_pass, expiresIn=86400, by_sms=True)

ticker = input("Enter a ticker: ")
spot_price = float(rs.robinhood.stocks.get_latest_price(ticker)[0])

options = []
expirations = []

for option in rs.robinhood.options.find_tradable_options(ticker):
    if option['expiration_date'] not in expirations:
        expirations.append(option['expiration_date'])

expirations.sort()
curr_exp = expirations[int(input("Enter an expiration: "))]
greek = input("Enter a greek: ")

total_call_ex = 0
total_put_ex = 0
pp = None
pn = None
call_ex_by_strike_and_exp = {}
put_ex_by_strike_and_exp = {}

options = rs.robinhood.options.find_options_by_expiration(ticker, curr_exp)
for option in options:
    spot_ex = 0
    
    if greek in option and option[greek]:
        spot_ex = float(option[greek]) * float(option['open_interest'])

    strike = float(option['strike_price'])
    
    if option['type'] == 'call':
        if not pp or spot_ex > call_ex_by_strike_and_exp[pp]:
            pp = strike
        
        call_ex_by_strike_and_exp[strike] = spot_ex
        total_call_ex += spot_ex
    elif option['type'] == 'put':
        if greek == 'delta':
            if not pn or spot_ex < put_ex_by_strike_and_exp[pn]:
                pn = strike

            put_ex_by_strike_and_exp[strike] = spot_ex
            total_put_ex += spot_ex
        elif greek == 'gamma':
            if not pn or -spot_ex < put_ex_by_strike_and_exp[pn]:
                pn = strike

            put_ex_by_strike_and_exp[strike] = -spot_ex
            total_put_ex -= spot_ex

call_ex_df = pd.DataFrame(call_ex_by_strike_and_exp.items(), columns=['Strike', 'EX']).sort_values(by='Strike')
put_ex_df = pd.DataFrame(put_ex_by_strike_and_exp.items(), columns=['Strike', 'EX']).sort_values(by='Strike')

pos_label = 'POS GEX: ' if greek == 'gamma' else 'POS DEX: '
neg_label = 'NEG GEX: ' if greek == 'gamma' else 'NEG DEX: '
ax = call_ex_df.plot(x='Strike', y='EX', color='green', label=pos_label + str(round(100 * total_call_ex / (total_call_ex - total_put_ex))) + '%')
put_ex_df.plot(ax=ax, x='Strike', y='EX', color='red', label=neg_label + str(round(100 * total_put_ex / (total_call_ex - total_put_ex))) + '%')

pos_label = 'PPG: ' if greek == 'gamma' else 'PPD: '
neg_label = 'PNG: ' if greek == 'gamma' else 'PND: '
plt.plot(pp, call_ex_by_strike_and_exp[pp], '*', markersize=12, color='green', label=pos_label + str(pp))
plt.plot(pn, put_ex_by_strike_and_exp[pn], '*', markersize=12, color='red', label=neg_label + str(pn))
plt.axvline(x = spot_price, color='black', linestyle='--', label='Current Price: ' + str(round(spot_price, 2)))

plt.legend()
plt.show()