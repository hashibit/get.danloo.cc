((python-mode . ((python-shell-interpreter . "uv")
                 (python-shell-interpreter-args . "run python")
                 (eglot-server-programs . ((python-mode . ("basedpyright-langserver" "--stdio"))))
                 (eglot-workspace-configuration
                  . ((:basedpyright
                      :settings (:python
                                 (:pythonPath ".venv/bin/python"
                                  :venvPath "."
                                  :venv ".venv")
                                 :analysis
                                 (:extraPaths ["./common" "./backend" "./process" "./ai-provider/ai-provider"]
                                  :autoSearchPaths t
                                  :useLibraryCodeForTypes t
                                  :autoImportCompletions t
                                  :typeCheckingMode "basic"))))))))