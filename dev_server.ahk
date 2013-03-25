SetWorkingDir %A_ScriptDir%
run, cmd
winwaitactive, ahk_class ConsoleWindowClass
send, dev_server.py --mysql=root:admin@localhost:3306 --storage-path storage{enter}