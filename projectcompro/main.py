import os
import struct
from datetime import datetime
from report import report_menu

# ==========================================
# CONSTANTS & CONFIGURATIONS
# ==========================================
# ขนาด fixed-length สำหรับฟิลด์
# Struct Format: < (Little-Endian)
# i  : comp_id (int4)
# 16s: pc_name (char[16])
# 16s: zone (char[16])
# i  : ram_gb (int4)
# f  : rate_per_hr (float4)
# 16s: status (char[16])
# ?  : is_active (bool1)
RECORD_FORMAT = "<i16s16sif16s?"
RECORD_SIZE = struct.calcsize(RECORD_FORMAT)

# กำหนดไฟล์ไบนารี 3 ไฟล์ และไฟล์รายงาน 1 ไฟล์
FILE_COMPUTERS = "computers.bin"
FILE_CUSTOMERS = "customers.bin"
FILE_BOOKINGS = "bookings.bin"
FILE_REPORT = "summary_report.txt"

# หน่วยความจำชั่วคราวสำหรับเก็บประวัติการทำงานล่าสุดในเซสชัน (Audit Log)
ACTION_LOGS = []


def log_action(action: str):
    """บันทึกประวัติการทำงานพร้อมประทับเวลา"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ACTION_LOGS.append(f"[{now_str}] {action}")


# ==========================================
# BINARY I/O FUNCTIONS (COMPUTER RECORD)
# ==========================================
def pack_computer_record(comp_id: int, pc_name: str, zone: str, ram_gb: int, 
                         rate_per_hr: float, status: str, is_active: bool) -> bytes:
    """แปลงข้อมูลคอมพิวเตอร์เป็น bytes ขนาด fixed-length ด้วย struct.pack"""
    return struct.pack(
        RECORD_FORMAT,
        comp_id,
        pc_name.encode('utf-8')[:16].ljust(16, b'\x00'),
        zone.encode('utf-8')[:16].ljust(16, b'\x00'),
        ram_gb,
        rate_per_hr,
        status.encode('utf-8')[:16].ljust(16, b'\x00'),
        is_active
    )


def unpack_computer_record(buffer: bytes) -> dict:
    """แปลง bytes กลับมาเป็น dictionary ข้อมูลคอมพิวเตอร์"""
    unpacked = struct.unpack(RECORD_FORMAT, buffer)
    return {
        "comp_id": unpacked[0],
        "pc_name": unpacked[1].decode('utf-8').rstrip('\x00'),
        "zone": unpacked[2].decode('utf-8').rstrip('\x00'),
        "ram_gb": unpacked[3],
        "rate_per_hr": unpacked[4],
        "status": unpacked[5].decode('utf-8').rstrip('\x00'),
        "is_active": unpacked[6]
    }


def init_data_files():
    """สร้างไฟล์ข้อมูลเปล่าเมื่อยังไม่มีไฟล์ โดยไม่ใส่ข้อมูลตัวอย่าง"""
    for file_path in (FILE_COMPUTERS, FILE_CUSTOMERS, FILE_BOOKINGS):
        if not os.path.exists(file_path):
            with open(file_path, "wb") as file:
                file.flush()
                os.fsync(file.fileno())


def read_all_computers() -> list[dict]:
    """อ่านระเบียนคอมพิวเตอร์ทั้งหมดจากไฟล์ไบนารี"""
    records = []
    if not os.path.exists(FILE_COMPUTERS):
        return records

    with open(FILE_COMPUTERS, "rb") as f:
        while chunk := f.read(RECORD_SIZE):
            if len(chunk) == RECORD_SIZE:
                records.append(unpack_computer_record(chunk))
    return records


# ==========================================
# INPUT VALIDATION HELPERS
# ==========================================
def input_int(prompt: str, min_val: int = None, max_val: int = None) -> int:
    """ตรวจสอบอินพุตตัวเลขจำนวนเต็ม"""
    while True:
        val_str = input(prompt).strip()
        try:
            val = int(val_str)
            if min_val is not None and val < min_val:
                print(f"[!] ค่าต้องไม่น้อยกว่า {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"[!] ค่าต้องไม่เกิน {max_val}")
                continue
            return val
        except ValueError:
            print("[!] อินพุตไม่ถูกต้อง: กรุณากรอกเป็นตัวเลขจำนวนเต็มเท่านั้น")


def input_float(prompt: str, min_val: float = None) -> float:
    """ตรวจสอบอินพุตตัวเลขทศนิยม"""
    while True:
        val_str = input(prompt).strip()
        try:
            val = float(val_str)
            if min_val is not None and val < min_val:
                print(f"[!] ค่าต้องไม่น้อยกว่า {min_val}")
                continue
            return val
        except ValueError:
            print("[!] อินพุตไม่ถูกต้อง: กรุณากรอกเป็นตัวเลขทศนิยมเท่านั้น")


def input_string(prompt: str, max_length: int = 15, choices: list = None) -> str:
    """ตรวจสอบอินพุตข้อความ พร้อมจำกัดความยาวและตัวเลือก"""
    while True:
        val = input(prompt).strip()
        if not val:
            print("[!] ข้อความต้องไม่เป็นค่าว่าง")
            continue
        if len(val.encode('utf-8')) > max_length:
            print(f"[!] ความยาวข้อความเกิน {max_length} ไบต์ (กรุณากรอกใหม่ให้สั้นลง)")
            continue
        if choices and val.lower() not in [c.lower() for c in choices]:
            print(f"[!] ค่าที่กรอกต้องเป็นหนึ่งในนี้เท่านั้น: {', '.join(choices)}")
            continue
        return val


# ==========================================
# REPORT GENERATION FUNCTION
# ==========================================
def generate_report(output_file: str = FILE_REPORT) -> str:
    """สร้างรายงานข้อความ (.txt) พร้อมข้อมูลสรุป ช่องว่าง และประวัติการทำงาน"""
    records = read_all_computers()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S (+07:00)")

    lines = []
    lines.append("Cyber Cafe Booking System - Computer Report")
    lines.append(f"Generated At : {now_str}")
    lines.append("App Version  : 1.0")
    lines.append("Endianness   : Little-Endian")
    lines.append("Encoding     : UTF-8 (fixed-length)")
    lines.append("")
    lines.append("+--------+------------+------------+----------+------------------+----------+--------+")
    lines.append("| CompID | PC Name    | Zone       | RAM (GB) | Rate (THB/Hour)  | Status   | Active |")
    lines.append("+--------+------------+------------+----------+------------------+----------+--------+")

    total_records = len(records)
    active_recs = [r for r in records if r["is_active"]]
    deleted_count = total_records - len(active_recs)

    in_use_count = sum(1 for r in active_recs if r["status"] == "In Use")
    available_count = sum(1 for r in active_recs if r["status"] == "Available")
    maint_count = sum(1 for r in active_recs if r["status"] == "Maint")

    rates = [r["rate_per_hr"] for r in active_recs]
    min_rate = min(rates) if rates else 0.0
    max_rate = max(rates) if rates else 0.0
    avg_rate = sum(rates) / len(rates) if rates else 0.0

    zone_counts = {}
    for r in active_recs:
        z = r["zone"]
        zone_counts[z] = zone_counts.get(z, 0) + 1

    # สร้างแถวข้อมูลตาราง
    for r in records:
        active_str = "Yes" if r["is_active"] else "No"
        line = (f"| {r['comp_id']:<6} | "
                f"{r['pc_name']:<10} | "
                f"{r['zone']:<10} | "
                f"{r['ram_gb']:<8} | "
                f"{r['rate_per_hr']:<16.2f} | "
                f"{r['status']:<8} | "
                f"{active_str:<6} |")
        lines.append(line)

    lines.append("+--------+------------+------------+----------+------------------+----------+--------+")
    lines.append("")
    lines.append("Summary (นับเฉพาะเครื่องสถานะ Active)")
    lines.append(f"- Total Computers (records) : {total_records}")
    lines.append(f"- Active Computers          : {len(active_recs)}")
    lines.append(f"- Deleted Computers         : {deleted_count}")
    lines.append(f"- Free Slots (Unused/Soft-Deleted) : {deleted_count}")
    lines.append(f"- Currently In Use          : {in_use_count}")
    lines.append(f"- Available Now             : {available_count}")
    lines.append(f"- Under Maintenance         : {maint_count}")
    lines.append("")
    lines.append("Rate Statistics (THB/Hour, Active only)")
    lines.append(f"- Min : {min_rate:.2f}")
    lines.append(f"- Max : {max_rate:.2f}")
    lines.append(f"- Avg : {avg_rate:.2f}")
    lines.append("")
    lines.append("Computers by Zone (Active only)")
    for z in sorted(zone_counts.keys()):
        lines.append(f"- {z:<10} : {zone_counts[z]}")

    # ประวัติการทำงานล่าสุด (Audit Logs)
    lines.append("")
    lines.append("Recent Activity Logs")
    if ACTION_LOGS:
        for log in ACTION_LOGS[-10:]:  # แสดงสูงสุด 10 รายการล่าสุด
            lines.append(f"- {log}")
    else:
        lines.append("- No activity recorded in current session.")

    report_content = "\n".join(lines)

    # เขียนลงไฟล์ .txt พร้อม flush & sync เพื่อความปลอดภัย
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_content)
        f.flush()
        os.fsync(f.fileno())

    return report_content


# ==========================================
# CRUD OPERATIONS
# ==========================================
def add_computer():
    """1) Add เพิ่มระเบียนคอมพิวเตอร์ใหม่ (พร้อมตรวจสอบ Free Slots)"""
    print("\n--- Add New Computer ---")
    comp_id = input_int("Enter CompID (e.g. 1011): ", min_val=1)
    
    records = read_all_computers()
    for r in records:
        if r["comp_id"] == comp_id:
            print(f"[!] Error: CompID {comp_id} มีอยู่ในระบบแล้ว ไม่สามารถเพิ่มซ้ำได้")
            return

    pc_name = input_string("Enter PC Name (e.g. PC-11): ", max_length=15)
    zone = input_string("Enter Zone (Standard/VIP): ", max_length=15, choices=["Standard", "VIP"])
    ram_gb = input_int("Enter RAM GB (e.g. 16, 32): ", min_val=1)
    rate_per_hr = input_float("Enter Rate (THB/Hour): ", min_val=0.0)
    status = input_string("Enter Status (Available/In Use/Maint): ", max_length=15, choices=["Available", "In Use", "Maint"])

    data = pack_computer_record(comp_id, pc_name, zone, ram_gb, rate_per_hr, status, True)

    # ค้นหา Slot ที่ถูก Soft Delete เพื่อเขียนทับ (Free List Reuse)
    free_slot_idx = None
    for idx, r in enumerate(records):
        if not r["is_active"]:
            free_slot_idx = idx
            break

    if free_slot_idx is not None:
        with open(FILE_COMPUTERS, "rb+") as f:
            f.seek(free_slot_idx * RECORD_SIZE)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        print(f"[✓] บันทึกข้อมูลคอมพิวเตอร์ใหม่สำเร็จ (เขียนทับ Free Slot ที่ {free_slot_idx})")
    else:
        with open(FILE_COMPUTERS, "ab") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        print("[✓] บันทึกข้อมูลคอมพิวเตอร์ใหม่ต่อท้ายไฟล์สำเร็จ")

    log_action(f"Added new computer CompID: {comp_id} ({pc_name})")


def update_computer():
    """2) Update แก้ไขระเบียนคอมพิวเตอร์"""
    print("\n--- Update Computer ---")
    comp_id = input_int("Enter CompID to Update: ", min_val=1)
    records = read_all_computers()
    found = False

    with open(FILE_COMPUTERS, "rb+") as f:
        for idx, r in enumerate(records):
            if r["comp_id"] == comp_id and r["is_active"]:
                found = True
                print(f"พบข้อมูลปัจจุบัน -> Name: {r['pc_name']} | Zone: {r['zone']} | RAM: {r['ram_gb']} | Rate: {r['rate_per_hr']} | Status: {r['status']}")
                print("(กด Enter หากไม่ต้องการแก้ไขค่านั้นๆ)")

                pc_name_in = input(f"New PC Name [{r['pc_name']}]: ").strip()
                pc_name = pc_name_in if pc_name_in else r['pc_name']

                zone_in = input(f"New Zone [{r['zone']}]: ").strip()
                zone = zone_in if zone_in else r['zone']

                ram_in = input(f"New RAM [{r['ram_gb']}]: ").strip()
                ram_gb = int(ram_in) if ram_in.isdigit() else r['ram_gb']

                rate_in = input(f"New Rate [{r['rate_per_hr']}]: ").strip()
                try:
                    rate_per_hr = float(rate_in) if rate_in else r['rate_per_hr']
                except ValueError:
                    rate_per_hr = r['rate_per_hr']

                status_in = input(f"New Status [{r['status']}]: ").strip()
                status = status_in if status_in else r['status']

                f.seek(idx * RECORD_SIZE)
                f.write(pack_computer_record(comp_id, pc_name, zone, ram_gb, rate_per_hr, status, True))
                f.flush()
                os.fsync(f.fileno())
                print("[✓] แก้ไขข้อมูลคอมพิวเตอร์เรียบร้อยแล้ว")
                log_action(f"Updated computer CompID: {comp_id}")
                break

    if not found:
        print("[!] ไม่พบ CompID นี้ หรือสถานะถูกลบไปแล้ว")


def delete_computer():
    """3) Delete ลบระเบียน (Soft Delete: เปลี่ยน is_active = False)"""
    print("\n--- Delete Computer ---")
    comp_id = input_int("Enter CompID to Delete: ", min_val=1)
    records = read_all_computers()
    found = False

    with open(FILE_COMPUTERS, "rb+") as f:
        for idx, r in enumerate(records):
            if r["comp_id"] == comp_id and r["is_active"]:
                found = True
                f.seek(idx * RECORD_SIZE)
                f.write(pack_computer_record(
                    r["comp_id"], r["pc_name"], r["zone"], 
                    r["ram_gb"], r["rate_per_hr"], r["status"], False
                ))
                f.flush()
                os.fsync(f.fileno())
                print(f"[✓] ลบระเบียน CompID {comp_id} เรียบร้อยแล้ว (Soft Delete / Marked Inactive)")
                log_action(f"Deleted computer CompID: {comp_id} (Soft Delete)")
                break

    if not found:
        print("[!] ไม่พบ CompID นี้ หรือระเบียนถูกลบไปแล้ว")


def view_menu():
    """4) View เมนูย่อยสำหรับการดูข้อมูล"""
    while True:
        print("\n--- 4) View Sub-Menu ---")
        print("  4.1) ดูรายการเดียว (Single Record)")
        print("  4.2) ดูทั้งหมด (View All)")
        print("  4.3) ดูแบบกรอง (Filter by Zone)")
        print("  4.4) สถิติโดยสรุป (Summary Stats)")
        print("  0) ย้อนกลับเมนูหลัก")
        
        choice = input("เลือกเมนูย่อย (0, 1-4): ").strip()
        records = read_all_computers()

        if choice in ["1", "4.1"]:
            cid = input_int("Enter CompID: ", min_val=1)
            rec = next((r for r in records if r["comp_id"] == cid), None)
            if rec:
                print(f"\nID: {rec['comp_id']} | Name: {rec['pc_name']} | Zone: {rec['zone']} | RAM: {rec['ram_gb']}GB | Rate: {rec['rate_per_hr']:.2f} THB | Status: {rec['status']} | Active: {rec['is_active']}")
                log_action(f"Viewed single record CompID: {cid}")
            else:
                print("[!] ไม่พบข้อมูล")

        elif choice in ["2", "4.2"]:
            report_text = generate_report()
            table_part = report_text.split("Summary")[0]
            print("\n" + table_part)
            log_action("Viewed all computer records")

        elif choice in ["3", "4.3"]:
            zone_filter = input_string("กรอกโซนที่ต้องการกรอง (Standard/VIP): ").strip().lower()
            filtered = [r for r in records if r["zone"].lower() == zone_filter and r["is_active"]]
            print(f"\n--- รายการในโซน {zone_filter.upper()} (Active) ---")
            if filtered:
                for r in filtered:
                    print(f"ID: {r['comp_id']} | Name: {r['pc_name']} | RAM: {r['ram_gb']}GB | Rate: {r['rate_per_hr']:.2f} | Status: {r['status']}")
            else:
                print("[!] ไม่พบข้อมูลในโซนนี้")
            log_action(f"Filtered records by zone: {zone_filter}")

        elif choice in ["4", "4.4"]:
            report_text = generate_report()
            summary_part = report_text[report_text.find("Summary"):]
            print("\n" + summary_part)
            log_action("Viewed summary statistics")

        elif choice == "0":
            break
        else:
            print("[!] ตัวเลือกไม่ถูกต้อง กรุณาเลือก 0 ถึง 4")


# ==========================================
# MAIN PROGRAM LOOP
# ==========================================
def main():
    init_data_files()

    while True:
        print("\n==========================================")
        print(" Cyber Cafe Booking System (Python File I/O)")
        print("==========================================")
        print("1) Add (เพิ่ม)")
        print("2) Update (แก้ไข)")
        print("3) Delete (ลบ)")
        print("4) View (ดู)")
        print("5) Generate Report (.txt)")
        print("6) Report Problem (รายงานปัญหา)")
        print("0) Exit (ออก)")

        choice = input("\nเลือกเมนูการทำงาน (0-6): ").strip()

        if choice == "1":
            add_computer()
        elif choice == "2":
            update_computer()
        elif choice == "3":
            delete_computer()
        elif choice == "4":
            view_menu()
        elif choice == "5":
            log_action("Generated text report manually")
            report = generate_report()
            print(f"\n[✓] สร้างรายงานและบันทึกไว้ที่ '{FILE_REPORT}' สำเร็จแล้ว!")
            print("\n" + report)
        elif choice == "6":
            report_menu(read_all_computers)
        elif choice == "0":
            log_action("Exited application safely")
            report = generate_report()
            print(f"\n[✓] สร้างรายงานอัตโนมัติ ({FILE_REPORT}) flush/sync และปิดโปรแกรมเรียบร้อยแล้ว")
            break
        else:
            print("[!] เมนูไม่ถูกต้อง กรุณากรอกตัวเลข 0 ถึง 6")


if __name__ == "__main__":
    main()