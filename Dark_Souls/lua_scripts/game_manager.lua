[ENABLE]
{$lua}

local file_path = "C:\\Users\\Laween\\OneDrive\\Desktop\\MSUM\\Spring_2025\\490\\Final_Project\\Dark_Souls\\FP-Machine-Learning\\Code\\data\\run_log.txt"

local PLAYER_HEALTH_PTR_STR = "[[[[DarkSoulsIII.exe+04543F60]+28]+3A0]+70]+90"
local BOSS_HEALTH_PTR_STR   = "[[[[[[[DarkSoulsIII.exe+049648F8]+98]+200]+28]+168]+10]+F0]+F28"

-- Counters and run state variables
local runCount = 0
local winCount = 0
local lossCount = 0
local runInProgress = false
local runStartTime = nil

-- Log a run to the file in append mode.
local function logRun(outcome, duration, finalPlayerHP, finalBossHP)
    local file = io.open(file_path, "a")
    if file then
        local timestamp = os.date("%Y-%m-%d %H:%M:%S")
        local line = string.format("%s, Run: %d, Outcome: %s, Duration: %d seconds, Final PlayerHP: %d, Final BossHP: %d\n",
                        timestamp, runCount, outcome, duration, finalPlayerHP, finalBossHP)
        file:write(line)
        file:close()
        print("[GameManager] Logged run: " .. line)
    else
        print("[GameManager] ERROR: Could not open log file for appending.")
    end
end

-- Main function that checks the run state every second.
local function checkRun()
    local playerHPAddr = getAddress(PLAYER_HEALTH_PTR_STR)
    local bossHPAddr   = getAddress(BOSS_HEALTH_PTR_STR)
    if not playerHPAddr or not bossHPAddr then
         --print("[GameManager] ERROR: Could not resolve one or more pointers.")
         return
    end

    local playerHP = readInteger(playerHPAddr) or -1
    local bossHP   = readInteger(bossHPAddr)   or -1

    -- If both are alive and a run hasn't started, start a new run.
    if playerHP > 0 and bossHP > 0 and not runInProgress then
         runInProgress = true
         runStartTime = os.time()
         --print("[GameManager] New run started at " .. os.date("%X", runStartTime))
    end

    -- If a run is in progress and one of them dies, the run is over.
    if runInProgress and (playerHP <= 0 or bossHP <= 0) then
         runCount = runCount + 1
         local outcome = ""
         if bossHP <= 0 then
             outcome = "win"
             winCount = winCount + 1
         elseif playerHP <= 0 then
             outcome = "loss"
             lossCount = lossCount + 1
         end
         local duration = os.time() - runStartTime
         --print(string.format("[GameManager] Run over: Outcome: %s, Duration: %d seconds", outcome, duration))
         logRun(outcome, duration, playerHP, bossHP)
         runInProgress = false
         runStartTime = nil
    end
end

-- Create and enable a timer that calls checkRun() every 0.1 second.
gameManagerTimer = createTimer(nil, false)
gameManagerTimer.Interval = 100  -- 100ms = 0.1 second
gameManagerTimer.OnTimer = checkRun
gameManagerTimer.setEnabled(true)
print("[GameManager] Timer enabled. Game manager active.")

{$asm}

[DISABLE]
{$lua}
if gameManagerTimer then
    gameManagerTimer.destroy()
    gameManagerTimer = nil
end
{$asm}
