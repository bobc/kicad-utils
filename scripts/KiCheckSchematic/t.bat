@echo off

rem some test caes

rem check project
rem KiCheckSchematic.py --proj c:\Python_progs\component_demo\demo\demo_STM32_new\demo_STM32.pro

rem check for grid alignment
rem KiCheckSchematic.py --proj c:\Python_progs\component_demo\demo\demo_STM32_new\demo_STM32.pro --check_grid

rem fix grid alignment
KiCheckSchematic.py --proj c:\Python_progs\component_demo\demo\demo_STM32_new\demo_STM32.pro --fix_grid
