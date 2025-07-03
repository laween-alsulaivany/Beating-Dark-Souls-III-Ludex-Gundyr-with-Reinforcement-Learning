[ENABLE]
{$lua}

local trigger_file = "C:\\Users\\Laween\\OneDrive\\Desktop\\MSUM\\Spring_2025\\490\\Final_Project\\Dark_Souls\\FP-Machine-Learning\\Code\\data\\reset_trigger.txt"


local function resetEnvironmentLua()
  local al = getAddressList()
  print("Killing player and waiting 20 seconds!")
  local PR = al.getMemoryRecordByDescription("prep")
  if PR then
    PR.Active = true
    print("prep triggered!")
  else
    print("prep record not found!")
  end


  print("Reset environment triggered via file.")


end

-- Timer callback that checks for the trigger file.
local function checkForResetTrigger()
  local file = io.open(trigger_file, "r")
  if file then
    io.close(file)
    resetEnvironmentLua()
    os.remove(trigger_file)
    print("Trigger file processed and removed.")
  end
end

-- Create a timer that checks every 1000ms (1 second)
resetTriggerTimer = createTimer(nil, false)
resetTriggerTimer.Interval = 1000
resetTriggerTimer.OnTimer = checkForResetTrigger
resetTriggerTimer.setEnabled(true)
print("Reset trigger timer enabled. Waiting for trigger file: " .. trigger_file)

{$asm}
[DISABLE]
{$lua}
if resetTriggerTimer then
  resetTriggerTimer.destroy()
  resetTriggerTimer = nil
end
{$asm}
