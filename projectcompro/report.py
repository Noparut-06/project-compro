import csv
import os
from datetime import datetime


FILE_ISSUES = "problem_reports.csv"
FIELDS = ("report_id", "comp_id", "pc_name", "description", "reported_at", "status")


def _read_reports() -> list[dict[str, str]]:
    if not os.path.exists(FILE_ISSUES):
        return []
    with open(FILE_ISSUES, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _write_reports(reports: list[dict[str, str]]) -> None:
    with open(FILE_ISSUES, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(reports)
        file.flush()
        os.fsync(file.fileno())


def _display_reports(reports: list[dict[str, str]]) -> None:
    print("\n+----------+--------+------------+--------------------------------+---------------------+----------+")
    print("| ReportID | CompID | PC Name    | Problem                        | Reported At         | Status   |")
    print("+----------+--------+------------+--------------------------------+---------------------+----------+")
    for report in reports:
        print(
            f"| {report['report_id']:<8} | {report['comp_id']:<6} | "
            f"{report['pc_name'][:10]:<10} | {report['description'][:30]:<30} | "
            f"{report['reported_at']:<19} | {report['status']:<8} |"
        )
    print("+----------+--------+------------+--------------------------------+---------------------+----------+")


def _add_report(computers: list[dict]) -> None:
    active_computers = [computer for computer in computers if computer["is_active"]]
    if active_computers:
        print("\nเครื่องที่ใช้งานอยู่:")
        for computer in active_computers:
            print(f"{computer['comp_id']} - {computer['pc_name']}")
        comp_id_text = input("CompID ที่พบปัญหา (0 = ปัญหาระดับระบบ): ").strip()
    else:
        comp_id_text = input("CompID ที่พบปัญหา (0 = ปัญหาระดับระบบ; ไม่มีเครื่องในระบบ): ").strip()

    if not comp_id_text.isdigit():
        print("[!] กรุณากรอก CompID เป็นจำนวนเต็ม")
        return

    comp_id = int(comp_id_text)
    if comp_id < 0:
        print("[!] CompID ต้องไม่น้อยกว่า 0")
        return

    computer = next(
        (item for item in active_computers if item["comp_id"] == comp_id),
        None,
    )
    if comp_id != 0 and computer is None:
        print("[!] ไม่พบ CompID ที่ใช้งานอยู่")
        return

    description = input("รายละเอียดปัญหา: ").strip()
    if not description:
        print("[!] รายละเอียดปัญหาต้องไม่เป็นค่าว่าง")
        return

    reports = _read_reports()
    report_id = max((int(item["report_id"]) for item in reports), default=0) + 1
    reports.append(
        {
            "report_id": str(report_id),
            "comp_id": str(comp_id) if comp_id else "System",
            "pc_name": computer["pc_name"] if computer else "System",
            "description": description,
            "reported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Open",
        }
    )
    _write_reports(reports)
    print(f"[✓] บันทึกรายงานปัญหา #{report_id} แล้ว")


def report_menu(read_computers) -> None:
    while True:
        print("\n--- 6) Problem Reports ---")
        print("1) Report a problem (แจ้งปัญหา)")
        print("2) View reports (ดูรายงานปัญหา)")
        print("0) Back (กลับเมนูหลัก)")
        choice = input("เลือกเมนูย่อย (0-2): ").strip()

        if choice == "1":
            _add_report(read_computers())
        elif choice == "2":
            reports = _read_reports()
            if reports:
                _display_reports(reports)
            else:
                print("ยังไม่มีรายงานปัญหา")
        elif choice == "0":
            break
        else:
            print("[!] ตัวเลือกไม่ถูกต้อง กรุณาเลือก 0 ถึง 2")
