# pointer_scanner.py
import time
import struct
import threading
from pymem import Pymem
from pymem.process import module_from_name

########################################
# Symbol Map
########################################
symbol_map = {
    "LockTgtMan": 0x7FF785A0DBE0,
    "WorldChrMan": 0x7FF785A0FDB8,
    "target_ptr": 0x7FF781281000
}

########################################
# PointerReader Class with Safety Nets
########################################


class PointerReader:
    def __init__(self, process_name: str):
        """
        Initializes a pymem handle to the target process (e.g. DarkSoulsIII.exe)
        and stores its base address.
        If attaching fails, sets pm = None and base_addr = 0 to avoid crashes later.
        """
        self.pm = None
        self.base_addr = 0
        try:
            self.pm = Pymem(process_name)
            self.base_addr = module_from_name(
                self.pm.process_handle, process_name).lpBaseOfDll
            print(
                f"👉✅ Attached to {process_name} | Base Address: {hex(self.base_addr)}")
        except Exception as e:
            print(f"👉❌ Could not attach to process '{process_name}': {e}")
            # pm stays None; base_addr stays 0. We'll do safe checks before usage.

    def _is_process_valid(self) -> bool:
        """
        Checks if the pymem handle is valid and the base address is nonzero.
        Returns True if OK, False otherwise.
        """
        if self.pm is None or self.base_addr == 0:
            return False
        return True

    ########################################
    # Main Resolve Functions
    ########################################
    def resolve(self, offsets, data_type="byte", debug=False):
        """
        Resolves a pointer chain starting from the module base.
        Returns the final value or -1 if something fails.
        """
        if not self._is_process_valid():
            print("👉❌ resolve(): Invalid process handle or base address.")
            return -1
        return self.resolve_from_address(self.base_addr, offsets, data_type, debug)

    def resolve_from_named_pointer(self, symbol_map, symbol_name, offsets, data_type="byte", debug=False):
        """
        Resolves pointer chains that start from a named base address.
        Returns final value or -1 on failure.
        """
        if symbol_name not in symbol_map:
            print(
                f"👉❌ Pointer symbol '{symbol_name}' not found in symbol_map.")
            return -1
        if not self._is_process_valid():
            print("👉❌ resolve_from_named_pointer(): Invalid process handle.")
            return -1
        base_address = symbol_map[symbol_name]
        return self.resolve_from_address(base_address, offsets, data_type, debug)

    def resolve_from_address(self, address, offsets, data_type="byte", debug=False):
        """
        Resolves a pointer chain starting from a custom base address.
        Returns the final value, or -1 if something fails.
        """
        if not self._is_process_valid():
            print("👉❌ resolve_from_address(): Invalid process handle.")
            return -1

        addr = address
        if debug:
            print(f"\n🔍 Starting resolution from {hex(addr)}")

        try:
            for i, offset in enumerate(offsets):
                addr += offset
                if debug:
                    print(f"  Step {i+1}: +{hex(offset)} → {hex(addr)}")

                # Dereference if not on the last offset
                if i != len(offsets) - 1:
                    addr = self.pm.read_ulonglong(addr)
                    if debug:
                        print(f"     👉✅ Dereferenced → {hex(addr)}")

                    # If it returns 0 or all F's, it's probably invalid, but we won't crash:
                    if addr == 0 or addr == 0xFFFFFFFFFFFFFFFF:
                        if debug:
                            print("     👉❌ Got invalid pointer (0 or -1).")
                        return -1

            # Finally, read the value at 'addr'
            return self._read_value(addr, data_type, debug)

        except Exception as e:
            if debug:
                print(f"  👉❌ Exception during pointer resolution: {e}")
            return -1

    def resolve_address(self, offsets, debug=False, max_retries=5, delay=1, name="unknown"):
        """
        Resolves an address from base + pointer chain, with retry logic.
        Returns the final address or -1 if it fails after retries.
        """
        if not self._is_process_valid():
            print(
                f"👉❌ resolve_address(): Invalid process handle. Cannot resolve {name}.")
            return -1

        for attempt in range(max_retries):
            addr = self.base_addr
            if debug:
                print(
                    f"\n📍 Resolving address for {name} (Attempt {attempt + 1}/{max_retries}):")

            try:
                for i, offset in enumerate(offsets):
                    addr += offset
                    if debug:
                        print(f"  Step {i+1}: +{hex(offset)} → {hex(addr)}")

                    if i != len(offsets) - 1:
                        addr = self.pm.read_ulonglong(addr)
                        if debug:
                            print(f"     👉✅ Dereferenced → {hex(addr)}")

                        # Check for obviously invalid pointer
                        if addr == 0 or addr == 0xFFFFFFFFFFFFFFFF:
                            if debug:
                                print("     👉❌ Invalid pointer found. Retrying...")
                            raise ValueError("Invalid pointer chain")

                # If we reach here, the address is presumably valid
                if debug:
                    print(f"👉✅ Resolved address for {name}: {hex(addr)}")
                return addr

            except Exception as e:
                if debug:
                    print(
                        f"resolve_address(): 👉❌ {name} failed at {hex(addr)}: {e}")
                time.sleep(delay)  # wait before retrying

        print(
            f"resolve_address(): 👉❌ Gave up resolving address for {name} after {max_retries} retries.")
        return -1

    ########################################
    # Reading / Writing
    ########################################
    def _read_value(self, addr, data_type, debug=False):
        """
        Safely reads a value of the requested data_type from addr.
        Returns the read value or -1 if an error happens.
        """
        try:
            if data_type == "byte":
                value = self.pm.read_uchar(addr)
            elif data_type == "4byte":
                value = self.pm.read_uint(addr)
            elif data_type == "int":
                value = self.pm.read_int(addr)
            elif data_type == "float":
                value = self.pm.read_float(addr)
            elif data_type == "double":
                value = self.pm.read_double(addr)
            elif data_type == "string":
                # Arbitrarily read 32 bytes; user can parse further if needed
                value = self.pm.read_string(addr, 32)
            else:
                if debug:
                    print(
                        f"👉❌ _read_value(): Unsupported data type '{data_type}'.")
                return -1

            if debug:
                print(f"  🎯 Final value ({data_type}) → {value}")
            return value

        except Exception as e:
            if debug:
                print(f"👉❌ _read_value() exception: {e}")
            return -1

    def update_address(self, offsets, name="unknown", max_retries=5, delay=0.5, debug=False):
        """
        Updates the address of a pointer by resolving it with retries.
        Returns the resolved address or -1 if it fails.
        """
        if not self._is_process_valid():
            print(
                f"👉❌ update_address(): process invalid. Cannot update '{name}'.")
            return -1

        addr = self.resolve_address(
            offsets, debug=debug, max_retries=max_retries, delay=delay, name=name)
        if addr == -1:
            print(
                f"update_address(): 👉❌ Failed to resolve address for {name} after {max_retries} retries.")
        else:
            if len(str(addr)) < 14 and debug:
                print(
                    f"update_address(): 👉❌ Address for {name} looks too short: {addr}.")
            if debug and addr != -1:
                print(
                    f"update_address(): 👉✅ Address for {name} resolved to {hex(addr)}.")
        return addr

########################################
# Helper Functions: write_value, etc.
########################################


def write_value(reader, pointer, value, data_type="int",
                name="unknown", max_retries=5, delay=0.5, debug=False):
    """
    Writes a value to the pointer's resolved address after updating it (with safety checks).
    Returns True if successful, False otherwise.
    """
    if reader is None or not reader._is_process_valid():
        print(f"👉❌ write_value(): Reader invalid. Cannot write '{name}'.")
        return False

    resolved_addr = reader.update_address(
        pointer, name=name, max_retries=max_retries, delay=delay, debug=debug)
    if resolved_addr == -1:
        print(f"👉❌ write_value(): Failed to resolve pointer for '{name}'.")
        return False

    try:
        if data_type == "int":
            reader.pm.write_int(resolved_addr, value)
        elif data_type == "float":
            reader.pm.write_float(resolved_addr, value)
        else:
            print(
                f"👉❌ write_value(): Unsupported data type '{data_type}' for '{name}'.")
            return False

        print(
            f"👉✅ Value {value} ({data_type}) written @ {hex(resolved_addr)} for '{name}'.")
        return True

    except Exception as e:
        print(f"👉❌ write_value(): Failed to write {value} for '{name}': {e}")
        return False


def write_float_using_address(reader, addr, value, debug=False, name="unknown"):
    """
    Writes a float value to a specific address. If 'addr' is -1 or invalid, it fails safely.
    Returns True if successful, False otherwise.
    """
    if reader is None or not reader._is_process_valid():
        print(
            f"👉❌ write_float_using_address(): Reader invalid. Cannot write '{name}'.")
        return False

    if addr == -1:
        print(f"👉❌ write_float_using_address(): Invalid address for '{name}'.")
        return False

    try:
        reader.pm.write_float(addr, value)
        if debug:
            print(
                f"👉✅ Float value {value} written @ {hex(addr)} (for '{name}')")
        return True
    except Exception as e:
        print(
            f"👉❌ write_float_using_address(): Failed to write float {value} for '{name}': {e}")
        return False

########################################
# Reinitialization Helper
########################################


def reinitialize_reader(process_name: str = "DarkSoulsIII.exe", wait_time=2.0):
    """
    Closes the old Pymem handle (if any), waits, then creates a fresh PointerReader.
    """
    global reader
    try:
        if reader and reader.pm:
            reader.pm.close()
    except:
        pass  # ignore errors

    time.sleep(wait_time)
    reader = PointerReader(process_name)
    print("👉✅ Reinitialized pointer reader after memory reload.")
    return reader

########################################
# Debug Helpers
########################################


def dump_floats_near(pm, address, size=0x200):
    """
    Debugging helper: dump floats around a memory address.
    """
    if pm is None or address == -1:
        print("👉❌ dump_floats_near(): Invalid pm or address.")
        return

    try:
        data = pm.read_bytes(address, size)
        for i in range(0, size, 4):
            val = struct.unpack("f", data[i:i+4])[0]
            print(f"{hex(address + i)} → {val:.6f}")
    except Exception as e:
        print(f"👉❌ dump_floats_near() error: {e}")

########################################
# Freeze Value Function
########################################


def freeze_value(reader, pointer, value, data_type="int", interval_ms=100):
    """
    Continuously writes a value (like CE's freeze).
    Returns a thread handle so you can .running = False to stop it.
    """
    def freezer():
        print(
            f"🧊 Freezing pointer {pointer} to value {value} every {interval_ms}ms...")
        try:
            while freezer_thread.running:
                if reader and reader._is_process_valid():
                    addr = reader.resolve_address(pointer)
                    if addr != -1:
                        try:
                            if data_type == "int":
                                reader.pm.write_int(addr, value)
                            elif data_type == "float":
                                reader.pm.write_float(addr, value)
                            elif data_type == "byte":
                                reader.pm.write_uchar(addr, value)
                        except Exception as inner_e:
                            print(f"👉❌ Freezer error while writing: {inner_e}")
                time.sleep(interval_ms / 1000.0)
        except Exception as e:
            print(f"👉❌ Freezer thread error: {e}")

    freezer_thread = threading.Thread(target=freezer)
    freezer_thread.daemon = True
    freezer_thread.running = True
    freezer_thread.start()
    return freezer_thread

########################################
# Example: Boss Flag Helpers
########################################


def get_boss_HP(reader):
    """
    Returns the boss HP, or -1 if it fails.
    """
    if reader.update_address([0x049648F8, 0x98, 0x200, 0x28, 0x168, 0x10, 0xF0, 0xF28],
                             name="boss HP") == -1:
        return -1
    return reader.resolve([0x049648F8, 0x98, 0x200, 0x28, 0x168, 0x10, 0xF0, 0xF28], data_type="int")


def get_player_HP(reader):
    """
    Returns the player's HP, or -1 on failure.
    """
    if reader.update_address([0x04543F60, 0x28, 0x3A0, 0x70, 0x90],
                             name="player HP") == -1:
        return -1
    return reader.resolve([0x04543F60, 0x28, 0x3A0, 0x70, 0x90], data_type="int")


def get_player_stamina(reader):
    """
    Returns the player's stamina (int), or -1 on failure.
    """
    # first we must update & resolve the final pointer
    if reader.update_address([0x04543F60, 0x28, 0x3A0, 0x70, 0x90],
                             name="player stamina") == -1:
        return -1

    final_addr = reader.resolve_address([0x04543F60, 0x28, 0x3A0, 0x70, 0x90])
    if final_addr == -1:
        return -1
    try:
        return reader.pm.read_int(final_addr + 0x18)
    except:
        return -1


def get_player_estus(reader):
    """
    Returns the player's Estus as an int, or -1 on failure.
    """
    if reader.update_address([0x04795348, 0x8, 0xE0, 0x48, 0x115, 0x5, 0x145, 0xA35],
                             name="Estus") == -1:
        return -1
    return reader.resolve([0x04795348, 0x8, 0xE0, 0x48, 0x115, 0x5, 0x145, 0xA35], data_type="int")


def get_playerX(reader):
    """
    Returns player's X as float, or -1 if fail.
    """
    if reader.update_address([0x04543F60, 0x28, 0x80],
                             name="player X") == -1:
        return -1
    return reader.resolve([0x04543F60, 0x28, 0x80], data_type="float")


def get_playerY(reader):
    """
    Returns player's Y as float, or -1 if fail.
    """
    if reader.update_address([0x04543F60, 0x28, 0x80],
                             name="player Y") == -1:
        return -1
    final_addr = reader.resolve_address([0x04543F60, 0x28, 0x80])
    if final_addr == -1:
        return -1
    try:
        return reader.pm.read_float(final_addr + 4)
    except:
        return -1


def get_playerZ(reader):
    """
    Returns player's Z as float, or -1 if fail.
    """
    if reader.update_address([0x04543F60, 0x28, 0x80],
                             name="player Z") == -1:
        return -1
    final_addr = reader.resolve_address([0x04543F60, 0x28, 0x80])
    if final_addr == -1:
        return -1
    try:
        return reader.pm.read_float(final_addr + 8)
    except:
        return -1


def get_playerAngle(reader):
    """
    Returns the player's angle as float, or -1 if fail.
    """
    if reader.update_address([0x04543F60, 0x28, 0x80],
                             name="player angle") == -1:
        return -1
    final_addr = reader.resolve_address([0x04543F60, 0x28, 0x80])
    if final_addr == -1:
        return -1
    try:
        return reader.pm.read_float(final_addr - 0xC)
    except:
        return -1


def get_player_in_boss_fight(reader):
    """
    Returns 1 if in boss fight, 0 if not, or -1 if we can't read it.
    """
    if reader.update_address([0x047572B8, 0xC0],
                             name="in boss fight") == -1:
        return -1
    val = reader.resolve([0x047572B8, 0xC0], data_type="byte")
    if val == -1:
        return -1
    return val


def get_boss_flag(reader):
    """
    Reads the current boss flag byte from [0x004752F68, 0x40, 0x9C0, 0xAE7].
    Returns True if bit #7 is set, False if not, or -1 if fail.
    """
    ptr = [0x004752F68, 0x40, 0x9C0, 0xAE7]
    if reader.update_address(ptr, name="boss flag") == -1:
        return -1
    raw_val = reader.resolve(ptr, data_type="byte")
    if raw_val == -1:
        return -1
    return bool(raw_val & 0x80)


def get_any_value(reader, pointer, data_type="int", name="unknown"):
    """
    Returns the value at the pointer's resolved address.
    Returns -1 if it fails.
    """
    if reader.update_address(pointer, name) == -1:
        return -1
    return reader.resolve(pointer, data_type=data_type)
########################################
# Helper: Teleport / Reset Boss Flag
########################################


def teleport_to_boss(reader):
    """
    Teleports the player to the Ludex Gundyr arena.
    """
    PlayerX_PTR = [0x04543F60, 0x28, 0x80]
    x_address = reader.update_address(PlayerX_PTR, name="PlayerX")
    if x_address == -1:
        print("👉❌ Could not teleport: invalid player X address.")
        return

    # Write X
    write_float_using_address(
        reader, x_address, 124.4503403, name="Teleport X")
    # Write Z
    write_float_using_address(
        reader, x_address + 4, -63.95353699, name="Teleport Z")
    # Write Y
    write_float_using_address(reader, x_address + 8,
                              555.809021, name="Teleport Y")
    # Write Angle
    write_float_using_address(
        reader, x_address - 0xC, -2.778103352, name="Teleport Angle")


def reset_boss_flag(reader, boss_flag_ptr=[0x004752F68, 0x40, 0x9C0, 0xAE7], debug=False):
    """
    Clears the top (7th) bit of the boss-defeated flag, forcing it to zero.
    If reading/writing fails, returns False (does not crash).
    """
    # 1) Update pointer
    if reader.update_address(boss_flag_ptr, name="boss_defeated_bit") == -1:
        print("👉❌ Failed to update boss-defeated pointer.")
        return False

    # 2) Read current byte
    current_val = reader.resolve(boss_flag_ptr, data_type="byte", debug=debug)
    if current_val == -1:
        print("👉❌ Failed to read boss-defeated value.")
        return False

    # 3) Clear bit 7
    new_val = current_val & 0x7F

    # 4) Write it back
    final_addr = reader.resolve_address(
        boss_flag_ptr, debug=debug, name="boss_defeated_bit")
    if final_addr == -1:
        print("👉❌ Failed to resolve final boss-defeated address.")
        return False

    try:
        reader.pm.write_uchar(final_addr, new_val)
        print(
            f"👉✅ Boss 'defeated' bit changed from 0x{current_val:02X} to 0x{new_val:02X} @ {hex(final_addr)}")
        return True
    except Exception as e:
        print(f"👉❌ Failed to write new boss-defeated value: {e}")
        return False


# -------------------------------
# Main Test Execution
# -------------------------------
if __name__ == "__main__":
    reader = PointerReader("DarkSoulsIII.exe")
    if not reader._is_process_valid():
        print("👉❌ Cannot proceed: game process not attached.")
    else:
        # Main pointers
        BossHP_PTR = [0x04750A98, 0x0, 0x88, 0x18, 0x28, 0x3A0, 0x70, 0x90]
        Estus_PTR = [0x04795348, 0x8, 0xE0, 0x48, 0x115, 0x5, 0x145, 0xA35]
        PlayerHP_PTR = [0x04543F60, 0x28, 0x3A0, 0x70, 0x90]
        PlayerX_PTR = [0x04543F60, 0x28, 0x80]
        Player_in_boss_fight_PTR = [0x047572B8, 0xC0]
        Boss_Defeated_Flag_PTR = [0x004752F68, 0x40, 0x9C0, 0xAE7]

        boss_x = [0x4750A98, 0x0, 0x88, 0x18, 0x2428, 0x80]
        # print(get_any_value(reader, boss_x, data_type="float", name="boss x"))
        # print(get_any_value(reader, boss_x, data_type="int", name="boss x"))
        # print(get_any_value(reader, boss_x, data_type="byte", name="boss x"))
        # print(get_any_value(reader, boss_x, data_type="4byte", name="boss x"))
        BossX_PTR = [0x04750A98, 0x0, 0x88, 0x18, 0x2428, 0x80]
        BossY_PTR = [0x04750A98, 0x0, 0x88, 0x18, 0x2428, 0x84]
        BossZ_PTR = [0x04750A98, 0x0, 0x88, 0x18, 0x2428, 0x88]
        # Likely quaternion or direct yaw
        BossAngle_PTR = [0x04750A98, 0x0, 0x88, 0x18, 0x2428, 0x90]
        BossAnimID_PTR = [0x04750A98, 0x0, 0x88, 0x18,
                          0x30, 0x68]   # Animation/behavior ID (int)
        # Just read this → if it's non-zero, you're locked on
        LockOnTarget_PTR = [0x04750A98]
        PlayerInBossFight_PTR = [0x047572B8, 0xC0]  # Already confirmed
        # Bit 7 is the "defeated" flag
        BossDefeatedFlag_PTR = [0x004752F68, 0x40, 0x9C0, 0xAE7]
        is_locked_on = reader.resolve(LockOnTarget_PTR, data_type="4byte") != 0

        print(f"Is locked on: {is_locked_on}")
        print(f"Boss HP: {get_boss_HP(reader)}")
        print(f"Player HP: {get_player_HP(reader)}")
        print(f"Player X: {get_playerX(reader)}")
        print(f"Player Y: {get_playerY(reader)}")
        print(f"Player Z: {get_playerZ(reader)}")
        print(f"Player Angle: {get_playerAngle(reader)}")
        print(f"Player Estus: {get_player_estus(reader)}")
        print(f"Player Stamina: {get_player_stamina(reader)}")
        print(f"Player in boss fight: {get_player_in_boss_fight(reader)}")
        print(f"Boss defeated flag: {get_boss_flag(reader)}")
        print(
            f"Boss X: {get_any_value(reader, BossX_PTR, data_type='float', name='boss x')}")
        print(
            f"Boss Y: {get_any_value(reader, BossY_PTR, data_type='float', name='boss y')}")
        print(
            f"Boss Z: {get_any_value(reader, BossZ_PTR, data_type='float', name='boss z')}")
        print(
            f"Boss Angle: {get_any_value(reader, BossAngle_PTR, data_type='float', name='boss angle')}")
        print(
            f"Boss Animation ID: {get_any_value(reader, BossAnimID_PTR, data_type='int', name='boss anim ID')}")

        # Backup pointers (preserved)
        # BossHP_PTR = [0x049648F8, 0x98, 0x200, 0x28, 0x168, 0x10, 0xF0, 0xF28]
        # PlayerX_PTR = [0x04753A48, 0x3A0, 0x3C8, 0x1E8, 0x590, 0x80]
        # PlayerHP_PTR = [0x04753A48, 0x3A0, 0x3C8, 0x1E8, 0x598, 0xD18]
        # PlayerHP_PTR = [0x04796898, 0x90, 0x100, 0x758, 0xD18]
        # PlayerHP_PTR = [0x0477FDB8, 0x80, 0x50, 0x3C8, 0x758, 0xD18]
        # PlayerHP_PTR = [0x0465CAF0, 0x38, 0x0, 0x98, 0xD18]
        # write_value(reader, [0x04543F60, 0x28, 0x3A0,
        #                      0x70, 0x90], 0, data_type="int", name="test")

        # print(time.strftime('%H:%M:%S'))
        # print(type(get_player_in_boss_fight(reader)))
        # print(type(get_boss_flag(reader)))
        # reset_boss_flag(reader)
        # print(get_boss_HP(reader))
        # teleport_to_boss(reader)
        # value = reader.resolve_from_named_pointer(
        #     symbol_map, "WorldChrMan", [0xD8, 0x18, 0x1F90, 0x80], data_type="4byte", debug=True)
        # print(f"Resolved value 1 starting from 0xD8: {value}")
        # value = reader.resolve_from_named_pointer(
        #     symbol_map, "WorldChrMan", [0x80, 0x1F90, 0x18, 0xD8], data_type="4byte", debug=True)
        # print(f"Resolved value 1 starting from 0x80: {value}")
        # value = reader.resolve_from_named_pointer(
        #     symbol_map, "LockTgtMan", [0x2821], data_type="byte", debug=True)
        # print(f"Resolved value 2: {value}")
        # value = reader.resolve_from_named_pointer(
        #     symbol_map, "WorldChrMan", [0x40, 0x28, 0x80], data_type="float", debug=True)
        # print(f"Resolved value 3: {value}")
        # value = reader.resolve_from_named_pointer(
        #     symbol_map, "target_ptr", [0x1F90, 0x68, 0xa8, 0x40, 0x70], data_type="float", debug=True)
        # print(f"Resolved value 4: {value}")

        # Resolve values
        # bossHP = reader.resolve(BossHP_PTR, data_type="int")

        # playerX = reader.resolve(PlayerX_PTR, data_type="float")
        # estus = reader.resolve(Estus_PTR, data_type="4byte")
        # playerHP = reader.resolve(PlayerHP_PTR, data_type="4byte")
        # hp_address = reader.resolve_address(PlayerHP_PTR)
        # playerMP = reader.pm.read_int(hp_address + 0xC)
        # playerStamina = reader.pm.read_int(hp_address + 0x18)
        # Player_in_boss_fight = reader.resolve(
        #     Player_in_boss_fight_PTR, data_type="byte")

        # print("\nPlayer Info:")
        # print("------------")
        # x_address = reader.resolve_address(PlayerX_PTR)
        # x, y, z, angle = read_xyz(reader.pm, x_address)
        # print(f"📍 X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}, Angle: {angle:.2f}")
        # print(f"💪 HP: {playerHP}, MP: {playerMP}, Stamina: {playerStamina}")
        # print(f"🧪 Estus: {estus}")

        # # Print boss info
        # print("\nBoss Info:")
        # print("------------")
        # print(f"🔍 BossHP: {bossHP}")

        # # print game stats:
        # print("\nGame Stats:")
        # print("------------")
        # print(f"🔍 in boss fight: {Player_in_boss_fight}")

        # flag = get_boss_flag(reader, Boss_Defeated_Flag_PTR)
        # if flag != -1:
        #     print("Boss flag value is:", flag)
        # print(int(get_player_in_boss_fight(reader)))
        # flag_value = get_boss_flag(reader, [0x004752F68, 0x40, 0x9C0, 0xAE7])
        # print(int(bool(flag_value & 0x80)))

        # this kills the player
        # write_value(reader, PlayerHP_PTR, 0)

        # this resets the boss flag
        # PointerReader.reset_boss_flag(reader, Boss_Defeated_Flag_PTR)

        # this teleports the player to the Ludex Gundyr arena
        # teleport_to_boss()

    #  print debugging
        # print(f"🔍 BossHP: {bossHP}")
        # print(f"🔍 PlayerX: {playerX}")
        # print(f"🔍 Estus: {estus}")
        # print(f"🔍 PlayerHP: {playerHP}")
        # print(f"🔍 PlayerMP: {playerMP}")
        # print(f"🔍 PlayerStamina: {playerStamina}")
        # print(f"🔍 Lockon: {lock}")
