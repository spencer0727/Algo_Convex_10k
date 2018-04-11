from collections import deque

# Put any initialization logic here.  The context object will be passed to
# the other methods in your algorithm.
def initialize(context):
    #using the NASDAQ100 etf
    context.ndx = sid(19920)
    #container to count the number of event windows we have cycled through
    context.ticks = 0
    #Wilder uses a rolling window of 14 days for various smoothing within
    #the indicator calculation
    context.window_length = 14
    #a collection of data containers that will be used during steps of the calculation
    context.highs = deque([0] * 2, 2)
    context.lows = deque([0] * 2, 2)
    context.closes = deque([0] * 2, 2)
    context.true_range_bucket = deque([0] * context.window_length, context.window_length)
    context.pDM_bucket = deque([0] * context.window_length, context.window_length)
    context.mDM_bucket = deque([0] * context.window_length, context.window_length)
    context.dx_bucket = deque([0] * context.window_length, context.window_length)
    #not sure why I had to define these here, but to print them later when debuggin
    #I found that I had to declare them here
    context.av_true_range = 0
    context.av_pDM = 0
    context.av_mDM = 0
    context.di_diff = 0
    context.di_sum = 0
    context.dx = 0
    context.adx = 0
    context.pDI = 0
    context.mDI = 0
    pass

# Will be called on every trade event for the securities you specify. 
def handle_data(context, data):
    #iterate event window counter
    context.ticks += 1 
    #pass high, low, close prices to our rolling containers
    context.highs.appendleft(data[sid(19920)].high)
    context.lows.appendleft(data[sid(19920)].low)
    context.closes.appendleft(data[sid(19920)].close_price)
    
    
    #ensure no calculation on first window
    if context.closes[0] == 0:
        high_less_low = 0
        high_less_prec_close = 0
        low_less_prec_close = 0
        high_less_prec_high = 0
        prec_low_less_low = 0
        pDM_one = 0
        mDM_one = 0
    else:
        high_less_low = context.highs[0]-context.lows[0]
        high_less_prec_close = abs(context.highs[0]-context.closes[1])
        low_less_prec_close = abs(context.lows[0]-context.closes[1])
        high_less_prec_high = context.highs[0]-context.highs[1]
        prec_low_less_low = context.lows[1]-context.lows[0]
    
    
    #calculate the Plus Directional Movement
    if high_less_prec_high > prec_low_less_low:
        pDM_one = max(high_less_prec_high,0)
    else:
        pDM_one = 0

    #calculate the Minus Directional Movement  
    if prec_low_less_low > high_less_prec_high:
        mDM_one = max(prec_low_less_low,0)
    else:
        mDM_one = 0
        
    #add the current pDM and mDM to the bucket to aid calculation of the first point in the
    #smoothed statistic
    context.pDM_bucket.appendleft(pDM_one)
    context.mDM_bucket.appendleft(mDM_one)
    
    #calculate the True Range and add to bucket
    true_range = max(high_less_low,high_less_prec_close,low_less_prec_close)
    context.true_range_bucket.appendleft(true_range)
    
    #once we have collected enough data to have populated the rolling windows adequately
    #we can start the meat of the calculation
    if context.ticks < (context.window_length + 1):
        context.av_true_range = 1
        context.av_pDM = 0
        context.av_mDM = 0
    elif context.ticks == (context.window_length + 1):
        context.av_true_range = sum(context.true_range_bucket)
        context.av_pDM = sum(context.pDM_bucket)
        context.av_mDM = sum(context.mDM_bucket)
    else:
        context.av_true_range = context.av_true_range - (context.av_true_range/context.window_length) + true_range 
        context.av_pDM = context.av_pDM - (context.av_pDM/14) + pDM_one
        context.av_mDM = context.av_mDM - (context.av_mDM/14) + mDM_one

    if context.ticks > context.window_length:    
        context.pDI = 100 * context.av_pDM / context.av_true_range
        context.mDI = 100 * context.av_mDM / context.av_true_range
        context.di_diff = abs(context.pDI - context.mDI)
        context.di_sum = context.pDI + context.mDI
        context.dx = 100 * context.di_diff / context.di_sum
        
    
    #add to bucket to provide an average of the DX figures that will
    #act as a starting point for the rolling ADX calculation
    context.dx_bucket.appendleft(context.dx)
    
    #the rolling ADX calculation
    if context.ticks == (context.window_length * 2):
        context.adx = sum(context.dx_bucket) / context.window_length
    elif context.ticks > (context.window_length * 2):
        context.adx = ((context.adx * (context.window_length - 1)) + context.dx) / context.window_length
    

    #simple ADX and DI based trading logic
    if (context.adx > 20) and (context.pDI > context.mDI):
        order(sid(19920), 500)
        log.debug('buy')
    elif (context.adx > 25) and (context.pDI < context.mDI):
        order(sid(19920), -500)
        log.debug('sell')
        
    log.debug('adx')
    log.debug(context.adx)
    log.debug('pDI')
    log.debug(context.pDI)
    log.debug('mDI')
    log.debug(context.mDI)