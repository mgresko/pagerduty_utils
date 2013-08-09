Pagerduty Utils
===============

How much time am I on call?

Percentage oncall for all users in last 60 days

```python
python total_oncall_time.py --schedule <schedule> --api-token <token> --pd-site <site> --start 60 --stop 0
```

Example Output
```
Total Minutes: 86400

test1@example.com: 42.69%
test2@example.com: 26.66%
test3@example.com: 26.60%
test4@example.com: 3.45%
test5@example.com: 0.49%
test6@example.com: 0.03%
```

Details: http://developer.pagerduty.com/documentation/rest/schedules
