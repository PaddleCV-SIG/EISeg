from qpt.executor import CreateExecutableModule

if __name__ == "__main__":
    module = CreateExecutableModule(
        work_dir="github/EISeg", 
        launcher_py_path="github/EISeg/eiseg/exe.py", 
        save_path="github/out"
    )
    module.make()