# Cockpit context injection

Cockpit surfaces a text box for context when raising a task signal from the GUI.
To give downstream automations the same structured data as the CLI, include the
job identifier and message on separate lines in the form:

```
Job: <task or job id>
Message: <status update or request>
```

When using the cockpit GUI, paste the ``Job`` line first, followed by the
``Message`` line. The CLI fall back uses the same structure:

```shell
# Equivalent CLI update
printf 'Job: %s\nMessage: %s\n' "my-task-id" "Waiting on vendor confirmation" \
  | tino task signal my-task-id --note - --confirm
```

The CLI example streams the formatted note to ``tino task signal`` using STDIN;
Cockpit mirrors this shape so automated parsers can detect the job id and
message fields consistently.
