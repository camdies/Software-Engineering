"""start_mysql.py - Start MySQL Portable and ensure database is ready.

Called by run.bat with the install root as the first argument.
All output is pure ASCII.  mysqld errors are logged to
mysql-portable/mysqld.log.
"""

import os
import sys
import time
import subprocess


def mysql_ready(mysql_exe):
    r = subprocess.run(
        [mysql_exe, "-u", "root", "-pCairenbin2005",
         "--protocol=TCP", "-e", "SELECT 1"],
        capture_output=True
    )
    return r.returncode == 0


def main():
    root = sys.argv[1]
    mysql_dir = os.path.join(root, "mysql-portable")

    if not os.path.isdir(mysql_dir):
        print("[ERROR] mysql-portable folder not found. Reinstall with MySQL component.")
        sys.exit(1)

    os.chdir(mysql_dir)

    auto_ini = os.path.join(mysql_dir, "my.ini.auto")
    mysql_exe = os.path.join(mysql_dir, "bin", "mysql.exe")
    mysqld_exe = os.path.join(mysql_dir, "bin", "mysqld.exe")
    data_dir = os.path.join(mysql_dir, "data")
    log_file = os.path.join(mysql_dir, "mysqld.log")
    sql_path = os.path.join(root, "backend", "config", "init_database_mysql.sql")
    config_path = os.path.join(root, "backend", "config", "config.ini")

    if not os.path.isfile(mysqld_exe):
        print("[ERROR] mysqld.exe not found. Reinstall with MySQL component.")
        sys.exit(1)

    # ---- my.ini.auto ----
    ini_tmpl = os.path.join(mysql_dir, "my.ini")
    if not os.path.isfile(ini_tmpl):
        print("[ERROR] my.ini template not found:", ini_tmpl)
        sys.exit(1)
    with open(ini_tmpl, "r", encoding="utf-8") as f:
        content = f.read()
    with open(auto_ini, "w", encoding="utf-8") as f:
        f.write(content.replace("CURRENT_DIR", mysql_dir))

    # ---- Update config.ini password ----
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = f.read()
        if "YOUR_MYSQL_PASSWORD" in cfg:
            cfg = cfg.replace("YOUR_MYSQL_PASSWORD", "Cairenbin2005")
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(cfg)

    # ---- First-time init ----
    data_empty = not os.path.exists(data_dir) or not os.listdir(data_dir)

    if data_empty:
        print("[1/2] First launch - initializing MySQL (~20 seconds)...")
        if os.path.exists(data_dir):
            import shutil
            shutil.rmtree(data_dir, ignore_errors=True)
            time.sleep(1)
        os.makedirs(data_dir, exist_ok=True)

        r = subprocess.run(
            [mysqld_exe, "--defaults-file=" + auto_ini,
             "--initialize-insecure", "--console"],
            capture_output=True
        )
        if r.returncode != 0:
            print("[ERROR] MySQL initialization failed (exit {})".format(r.returncode))
            err = r.stderr.decode("utf-8", errors="replace")
            if err.strip():
                print("[ERROR]", err[-800:])
            sys.exit(1)

        # Start temp MySQL — log stderr to file for diagnostics
        fh = open(log_file, "wb")
        try:
            p = subprocess.Popen(
                [mysqld_exe, "--defaults-file=" + auto_ini, "--console"],
                stdout=fh, stderr=subprocess.STDOUT
            )
        except OSError as e:
            print("[ERROR] Cannot start mysqld.exe — VC++ Redist 2015-2022 may be missing.")
            print("[ERROR]", e)
            fh.close()
            sys.exit(1)

        for i in range(30):
            time.sleep(1)
            r = subprocess.run(
                [mysql_exe, "-u", "root", "--protocol=TCP", "-e", "SELECT 1"],
                capture_output=True
            )
            if r.returncode == 0:
                break
            if p.poll() is not None:
                fh.close()
                with open(log_file, "rb") as lf:
                    tail = lf.read()[-800:]
                print("[ERROR] mysqld.exe exited prematurely (exit {})".format(p.returncode))
                print("[ERROR] Log tail:", tail.decode("utf-8", errors="replace"))
                sys.exit(1)
        else:
            fh.close()
            p.terminate()
            print("[ERROR] MySQL startup timed out (30 seconds).")
            with open(log_file, "rb") as lf:
                tail = lf.read()[-800:]
            print("[ERROR] Log tail:", tail.decode("utf-8", errors="replace"))
            sys.exit(1)

        fh.close()

        # Set root password
        subprocess.run(
            [mysql_exe, "-u", "root", "--protocol=TCP", "-e",
             "ALTER USER 'root'@'localhost' IDENTIFIED BY 'Cairenbin2005'; FLUSH PRIVILEGES;"],
            capture_output=True
        )

        # Import database
        with open(sql_path, "r", encoding="utf-8") as f:
            sql = f.read()
        r = subprocess.run(
            [mysql_exe, "-u", "root", "-pCairenbin2005",
             "--default-character-set=utf8mb4"],
            input=sql.encode("utf-8"), capture_output=True
        )
        if r.returncode != 0:
            err = r.stderr.decode("utf-8", errors="replace")
            print("[WARN] DB import had errors:", err[:500])

        # Restart MySQL
        subprocess.run(
            [mysql_exe, "-u", "root", "-pCairenbin2005",
             "--protocol=TCP", "-e", "SHUTDOWN"],
            capture_output=True
        )
        p.wait()
        time.sleep(3)
        print("   Database initialized successfully")

    # ---- Start MySQL (if not already running) ----
    if mysql_ready(mysql_exe):
        print("   MySQL ready")
        return

    fh = open(log_file, "ab")
    try:
        subprocess.Popen(
            [mysqld_exe, "--defaults-file=" + auto_ini, "--console"],
            stdout=fh, stderr=subprocess.STDOUT
        )
    except OSError as e:
        print("[ERROR] mysqld.exe failed to start — VC++ Redist 2015-2022 missing?")
        print("[ERROR]", e)
        fh.close()
        sys.exit(1)

    for i in range(20):
        time.sleep(1)
        if mysql_ready(mysql_exe):
            break
    else:
        fh.close()
        print("[ERROR] MySQL did not become ready within 20 seconds.")
        print("[ERROR] See log:", log_file)
        with open(log_file, "rb") as lf:
            tail = lf.read()[-1000:]
        print("[ERROR] Log tail:", tail.decode("utf-8", errors="replace"))
        sys.exit(1)

    fh.close()
    print("   MySQL ready")


if __name__ == "__main__":
    main()
