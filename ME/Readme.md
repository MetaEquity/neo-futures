# Intro
"""
CoinMarketCap Ticker API provides ticker updates for NEO-USD and other pairings
roughly every 5 minutes. There is no guarantee on the timestep (it's not exactly 5 minutes)

The Blockchain (i.e. Smart Contract) won't know the exact timestamp when CMC Ticker will update.

Instead, use the following approach:
T_0 = 1519544672 # arbitrary starting time
T_0_CMC = first timestamp > T_0 when CMC's Ticker updates
Oracles submit (T_0, T_0_CMC, Prediction) before T_1
T_1 = T_0 + 6 minutes (480 seconds)

----T_n---T_n_CMC------------T_n+1-----------
"""


# Algorithm Description
"""
1. Create a new game type (e.g. retrieve the price of NEO in USD at a certain time from the Coin Market Cap API Ticker)
2. Oracle can send in a value for NEO-USD for T_n between T_n and T_n+1, as well as sending in collateral
3. Anyone can try to 'get_prediction' for T_n, the first time this occurs it triggers the judging event
4. After Judging happens, 'get_prediction' returns the judged value

Note: to avoid getting penalised for latency,
The Oracle sends in the T_n they are applying for. If it is before T_n or after T_n+1, they will lose the collateral
they sent in for this application but not any balances they've accumulated


"""

# Some general concepts

"""
   [[Oracle balance]]
   There is a NEO-GAS balance maintained within the Smart Contract that represents how much the Oracle has
   This balance must be > 5 NEO-GAS in order to register
   You can register by sending in 5 NEO-GAS along with your register request
   Everyone has an Available Balance and a Locked Balance
   N.B. We did not implement in this phase of development using --attach-gas=5
   Instead, we just mocked it by allowing an extra parameter for 'gas' in submit_prediction
   This will be replaced by NEP-5 or attach-gas in future versions
   
   [[Judging]]
   The design of this smart contract is that every submission updates the state of the smart contract
   such that you maintain knowledge of the current winning prediction
   based on the most frequent prediction so far
   This means that the judging step is quite easy as you know already the winning prediction
   You just need to separate the winners from the losers
      
"""

# Smart Contract Operations
"""
   create_new_game {{client}} {{game_type}}
   > creates a new game type if it isn't currently 'live'
   
   submit_prediction {{oracle}} {{game_type}} {{instance_ts}} {{prediction}} {{gas-submission}}
   > submits prediction for game instance as long as balance is high enough (including any gas sent with this transaction)
      
   get_prediction {{game_type}} {{instance_ts}}
   > gets finalised prediction for specific instance by judging or retrieving if already judged
   
   get_available_balance_oracle {{oracle}}
   > gets available balance for oracle (excludes balance pledged to an as-yet unjudged instance)
   
   get_correct_oracles_for_instance {{game_type}} {{instance_ts}}
   > gets number of oracles who went with the majority option
   
   debug_get_value {{key}}
   > debug the smart contract for ease, key lookup in getcontext
   
   judge_instance {{game_type}} {{instance_ts}}
   > judge the instance if time is passed the deadline and not yet judged

"""
