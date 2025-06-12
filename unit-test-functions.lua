local functions = {}

-- potential return values:
functions.test_successful = 0 -- unit test succeeded.
functions.test_failed = 1 -- unit test failed.
functions.test_invalid = 2 -- unit testing structure failed.
functions.test_unfinished = 3 -- unit test is not finished yet.

function functions.print_msg(msg, indentation)
  -- indentation should not be used by unit tests, this is only used for the unit test interface!
  indentation = indentation and indentation >= 0 and math.floor(indentation + 0.5) or 2
  print("factorio-unit-test:" .. string.format("%" .. 2 * indentation + 1 .. "s", " ") .. msg)
end

function functions.assert(condition, msg)
  -- Dummy function as actually covered by macro in unit_test_controller.py
end

function functions.assert_equal(expression1, expression2)
  -- Dummy
end

return functions
