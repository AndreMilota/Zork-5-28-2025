## Guidance

- Remember to activate the venv before installing dependencies or running the project (the exact command may vary by OS).
- If you need to debug what the graph is doing, you can add debug=True to the graph.stream() call.
- Always test your changes before opening a pull request.
- You may test by piping your inputs into main.py like so:
    ```bash
    python main.py <<'EOF'
    go east
    go west
    exit
    EOF
    ```
