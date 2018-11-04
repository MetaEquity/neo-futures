# -*- coding: utf-8 -*-
"""
Created on Sat Nov  3 17:03:37 2018

@author: theki
"""
from boa.code.builtins import concat
from boa.blockchain.vm.Neo.Storage import GetContext, Get, Put
from boa.blockchain.vm.Neo.Blockchain import GetHeight, GetHeader
from boa.blockchain.vm.Neo.Header import GetTimestamp, GetNextConsensus
from boa.blockchain.vm.Neo.Runtime import Log, Notify, GetTrigger, CheckWitness
from neo_futures import KeepRefs,Game_rules

key_prefix_game_type = "game_type::"
key_prefix_game_instance = "game_instance::"
key_prefix_game_instance_prediction = "prediction::"
key_prefix_game_instance_judged = "judged::"
key_prefix_game_instance_max = "max::"
key_prefix_game_instance_index = "index::"
key_prefix_game_instance_count = "count::"
key_prefix_game_instance_correct_count = "correct_count::"
key_prefix_game_instance_oracle = "oracle::"
key_prefix_oracle = "oracle_address::"
key_prefix_agent_available_balance = "agent_available_balance::"
key_prefix_agent_locked_balance = "agent_locked_balance::"

class Game(KeepRefs):
    
    """ Start a Game"""
    def __init__(self,client_hash,instance_ts,Live=False,Oracles=[],Predictions=[],Winners=[]):
        self.ID=client_hash
        self.instance_ts=instance_ts
    
    def isGameTypeLive(game_type):
        key = concat(key_prefix_game_type, game_type)
        context = GetContext()
        v = Get(context, key)
        if v == 0:
            return False
        else:
            return True
        
    """General instance properties"""
        
    def GetCurrentMax(game_type, instance_ts):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        key = concat(k12, key_prefix_game_instance_max)
        context = GetContext()
        v = Get(context, key)
        Log(key)
        Log(v)
        return v
    
    def UpdateMaxVotes(game_type, instance_ts, p_count):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        key = concat(k12, key_prefix_game_instance_max)
        context = GetContext()
        Put(context, key, p_count)
            
    """Manage Oracles:Setters"""   
        
    def RegisterOracle(game_type, instance_ts, oracle, slot_n):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k3 = concat(key_prefix_game_instance_index, slot_n)
        k12 = concat(k1, k2)
        key = concat(k12, k3)
        # This registers the Oracle in the nth slot
        context = GetContext()
        Log("Register Oracle at N")
        Put(context, key, oracle)
        k4 = concat(key_prefix_game_instance_oracle, oracle)
        key = concat(k12, k4)
        # This registers the Oracle in the Game Instance
        context = GetContext()
        Log("Register Oracle for Instance")
        Put(context, key, 1)
        # This updates the counter
        key = concat(k12, key_prefix_game_instance_count)
        context = GetContext()
        Log("Update Counter")
        Put(context, key, slot_n)
        return True
    
    def SetCorrectOracleCountForInstance(game_type, instance_ts, correct_count):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        key = concat(k12, key_prefix_game_instance_correct_count)
        context = GetContext()
        Put(context, key, correct_count)
        
    """Manage Oracles:Getters"""
    
    def isOracleRegisteredForInstance(game_type, instance_ts, oracle):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        k4 = concat(key_prefix_game_instance_oracle, oracle)
        key = concat(k12, k4)
        context = GetContext()
        v = Get(context, key)
        if v == 0:
            return False
        else:
            return True

    def GetOracleAtIndexN(game_type, instance_ts, index):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k3 = concat(key_prefix_game_instance_index, index)
        k12 = concat(k1, k2)
        key = concat(k12, k3)
        # This registers the Oracle in the nth slot
        context = GetContext()
        v = Get(context, key)
        return v
    def GetOracleCountForInstance(game_type, instance_ts):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        key = concat(k12, key_prefix_game_instance_count)
        context = GetContext()
        v = Get(context, key)
        return v

    def GetCorrectOracleCountForInstance(game_type, instance_ts):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        key = concat(k12, key_prefix_game_instance_correct_count)
        context = GetContext()
        v = Get(context, key)
        return v


    
    """Manage Predictions:Setters"""
    # submit_prediction {{oracle}} {{game_type}} {{instance_ts}} {{prediction}} {{gas-submission}}
    def SubmitPrediction(self,oracle, game_type, instance_ts, prediction, gas_submission):
    
        #Add in auto-judging
        prev_instance = instance_ts - Game_rules.timestep
        self.JudgeInstance(game_type,prev_instance)
    
        # Trivial TODO
        # ADD IN GAME_TYPE CHECK
    
        Log("gas_submission")
        Log(gas_submission)
    
        # Check T_n relative to current TS()
        height = GetHeight()
        hdr = GetHeader(height)
        ts = GetTimestamp(hdr)
        Log(ts)
        t_n_plus_one = instance_ts + Game_rules.timestep
        Log(t_n_plus_one)
        Log(instance_ts)
        if ts > t_n_plus_one:
            #return 1  # expired
            Log("expired")
        elif ts < instance_ts:
            #return 2  # too early to submit, ignore
            Log("too early")
        else:
            #return 0  # all good
            Log("Sweet spot")
    
        Log(instance_ts)
    
        if self.isGameInstanceJudged(game_type, instance_ts):
            return "Game Instance already judged" # Ignore submission
        else:
    
            # ASSERT: current timestamp is in the sweet spot between T_n and T_n+1
    
            # Check if Oracle already registered
            if self.isOracleRegisteredForInstance(game_type, instance_ts, oracle):
                return "Already registered"
            current_oracle_balance = self.GetOracleBalance(oracle)
            n_oracles_for_instance = self.GetOracleCountForInstance(game_type, instance_ts)
            Log(gas_submission)
            if gas_submission == 0:
                if current_oracle_balance >= Game_rules.collateral_requirement:
                    new_count = n_oracles_for_instance + 1
                    self.RegisterOracle(game_type, instance_ts, oracle, new_count)
                else:
                    # No assets sent and existing balance too low
                    return "Not enough balance to register"
            elif gas_submission == 5:
                    Log(current_oracle_balance)
                    current_oracle_balance = current_oracle_balance + gas_submission
                    Log(current_oracle_balance)
                    key = concat(key_prefix_agent_available_balance, oracle)
                    Log("updating balance")
                    # Updates Balance of Oracle
                    context = GetContext()
                    Put(context, key, current_oracle_balance)
                    new_count = n_oracles_for_instance + 1
                    Log(new_count)
                    self.RegisterOracle(game_type, instance_ts, oracle, new_count)
                    Log("registered oracle")
            else:
                return "Wrong amount of NEO GAS Sent"
    
            locked = self.GetOracleLockedBalance(oracle)
            new_locked = locked + 5
            self.UpdateLockedBalance(oracle, new_locked)
            new_available = current_oracle_balance - 5
            self.UpdateAvailableBalance(oracle, new_available)
    
            # Now to submit prediction if no errors
            self.RegisterPrediction(game_type, instance_ts, oracle, prediction)
            p_count = self.IncrementCountForPrediction(game_type, instance_ts, prediction)
            Log("Registered and incremented pcount")
            max_so_far = self.GetCurrentMax(game_type, instance_ts)
            Log("max and pcount:")
            Log(max_so_far)
            Log(p_count)
            if p_count > max_so_far:
                # New Current Winner
                self.UpdateMaxVotes(game_type, instance_ts, p_count)
                self.UpdatePrediction(game_type, instance_ts, prediction)
            return True

    def RegisterPrediction(game_type, instance_ts, oracle, prediction):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        k3 = concat(key_prefix_game_instance_oracle, oracle)
        k123 = concat(k12, k3)
        key = concat(k123, key_prefix_game_instance_prediction)
        context = GetContext()
        Put(context, key, prediction)
        
    def UpdatePrediction(game_type, instance_ts, prediction):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        key = concat(k12, key_prefix_game_instance_prediction)
        context = GetContext()
        Put(context, key, prediction)
        
    def IncrementCountForPrediction(game_type, instance_ts, prediction):
    # Get current count
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        k3 = concat(key_prefix_game_instance_prediction, prediction)
        key = concat(k12, k3)
        context = GetContext()
        p_count = Get(context, key)
        if p_count == 0:
            p_count = 1
        else:
            p_count = p_count + 1
        context = GetContext()
        Put(context, key, p_count)
        return p_count
    
    """Manage Predictions:Getters"""
    def GetOraclePrediction(game_type, instance_ts, oracle):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        k3 = concat(key_prefix_game_instance_oracle, oracle)
        k123 = concat(k12, k3)
        key = concat(k123, key_prefix_game_instance_prediction)
        context = GetContext()
        v = Get(context, key)
        return v  
    
    
    def GetPrediction(game_type, instance_ts):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        key = concat(k12, key_prefix_game_instance_prediction)
        context = GetContext()
        v = Get(context, key)
        return v
        
   
    """Judge instance"""  
    # judge_instance {{game_type}} {{instance_ts}}
    
    def isGameInstanceJudged(game_type, instance_ts):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        key = concat(k12, key_prefix_game_instance_judged)
        context = GetContext()
        v = Get(context, key)
        if v == 0:
            return False
        else:
            return True
        
    def JudgeInstance(self,game_type, instance_ts):
        if self.isGameInstanceJudged(game_type, instance_ts):
            return "Already Judged"
        # Separate Winners from Losers
        correct_prediction = self.GetPrediction(game_type, instance_ts)
        n_oracles_for_instance = self.GetOracleCountForInstance(game_type, instance_ts)
        n_correct = 0
        total_bounty = 0
    
        index = 0
        while index < n_oracles_for_instance:
            index = index + 1
            oracle = self.GetOracleAtIndexN(game_type, instance_ts, index)
            oracle_prediction = self.GetOraclePrediction(game_type, instance_ts, oracle)
            if oracle_prediction == correct_prediction:
                # Add to Winners
                # collateral is moved from locked into available
                self.UnlockCollateral(oracle)
                n_correct = n_correct + 1
            else:
                # Add to Losers
                # Both Available and Locked Balance is removed and added to Winner collection
                oracle_available_balance = self.GetOracleBalance(oracle)
                oracle_locked_balance = self.GetOracleLockedBalance(oracle)
    
                total_bounty = total_bounty + oracle_available_balance + oracle_locked_balance
                self.WipeOutBalances(oracle)
    
        if n_correct == 0:
            return "Nothing correct"
    
        bounty_per_correct_oracle = total_bounty // n_correct
        owner_bounty = total_bounty % n_correct
        self.AddBountyForOwner(owner_bounty)
    
        Log("n_correct")
        Log(n_correct)
    
        self.SetCorrectOracleCountForInstance(game_type, instance_ts, n_correct)
    
        # Loop again
        index = 0
        while index < n_oracles_for_instance:
            index = index + 1
            oracle = self.GetOracleAtIndexN(game_type, instance_ts, index)
            oracle_prediction = self.GetOraclePrediction(game_type, instance_ts, oracle)
            if oracle_prediction == correct_prediction:
                oracle_available_balance = self.GetOracleBalance(oracle)
                oracle_available_balance = self.oracle_available_balance + bounty_per_correct_oracle
                self.UpdateAvailableBalance(oracle, self.oracle_available_balance)
    
        sep = "SEPARATOR"
        notification = concat(instance_ts, sep)
        notification = concat(notification, n_correct)
        notification = concat(notification, sep)
        notification = concat(notification, correct_prediction)
        Notify(notification)
        # Set Game to be Judged (no more judging allowed)
        self.SetGameInstanceJudged(game_type, instance_ts)
        return True
    
    def SetGameInstanceJudged(game_type, instance_ts):
        k1 = concat(key_prefix_game_type, game_type)
        k2 = concat(key_prefix_game_instance, instance_ts)
        k12 = concat(k1, k2)
        key = concat(k12, key_prefix_game_instance_judged)
        context = GetContext()
        Put(context, key, 1)
    
    
    
    """ Manage Balance/Rewards"""
    
    def GetOracleBalance(oracle):
        key = concat(key_prefix_agent_available_balance, oracle)
        context = GetContext()
        v = Get(context, key)
        return v
    
    def GetOracleLockedBalance(oracle):
        key = concat(key_prefix_agent_locked_balance, oracle)
        context = GetContext()
        v = Get(context, key)
        return v
    
    # Transfers collateral from locked to available
    def UnlockCollateral(self,oracle):
        available = self.GetOracleBalance(oracle)
        locked = self.GetOracleLockedBalance(oracle)
        new_available = available + Game_rules.collateral_requirement
        new_locked = locked - Game_rules.collateral_requirement
        self.UpdateAvailableBalance(oracle, new_available)
        self.UpdateLockedBalance(oracle, new_locked)
    
    def UpdateAvailableBalance(oracle, balance):
        key = concat(key_prefix_agent_available_balance, oracle)
        context = GetContext()
        Put(context, key, balance)
    
    def UpdateLockedBalance(oracle, balance):
        key = concat(key_prefix_agent_locked_balance, oracle)
        context = GetContext()
        Put(context, key, balance)
    
    def LockCollateral(self,oracle):
        available = self.GetOracleBalance(oracle)
        locked = self.GetOracleLockedBalance(oracle)
        new_available = available - Game_rules.collateral_requirement
        new_locked = locked + Game_rules.collateral_requirement
        self.UpdateAvailableBalance(oracle, new_available)
        self.UpdateLockedBalance(oracle, new_locked)
    
    def WipeOutBalances(self,oracle):
        self.UpdateAvailableBalance(oracle, 0)
        self.UpdateLockedBalance(oracle, 0)
    
    def AddBountyForOwner(self,owner_bounty):
        current_balance = self.GetOracleBalance(Game_rules.owner)
        new_balance = current_balance + owner_bounty
        self.UpdateAvailableBalance(Game_rules.owner, new_balance)
