[ENABLE]
{$lua}

-- Lock-on check Lua script for Cheat Engine
local lockTgtManBase = getAddress("LockTgtMan")  -- This is the base pointer
local offset = 0x2821
local checkInterval = 50 -- 1000ms = 1 second
local lockOnFilePath = "C:\\Users\\Laween\\OneDrive\\Desktop\\MSUM\\Spring_2025\\490\\Final_Project\\Dark_Souls\\FP-Machine-Learning\\Code\\data\\lock_on.txt"

function checkLockStatus()
    local lockStatusAddress = readPointer(lockTgtManBase) + offset
    local value = readBytes(lockStatusAddress, 1)

    local file = io.open(lockOnFilePath, "w")
    if value == 1 then
        file:write("locked")
    else
        file:write("nolock")
    end
    file:close()
end

-- Create a timer to call the check function every second
local timer = createTimer(nil, false)
timer.Interval = checkInterval
timer.OnTimer = checkLockStatus
timer.setEnabled(true)


{$asm}

[DISABLE]
{$lua}
{$asm}
