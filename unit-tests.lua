local unit_test_names = require("temp-test-list")

local unit_tests = {}

for _, unit_test_name in ipairs(unit_test_names) do
  local unit_test_path = "temp." .. unit_test_name
  local status, unit_test_funcs = pcall(require, unit_test_path)
  if status then
    for name, unit_test_func in pairs(unit_test_funcs) do
      if type(unit_test_func) == "function" then
        unit_tests[name] = unit_test_func
      else
        error(string.format("Unit test '%s' is not a function!", name))
      end
    end
  else
    error(string.format("Failed to load unit test '%s'", unit_test_name))
  end
end

local unit_test_functions = require("unit-test-functions")

local unit_tests_result = unit_test_functions.test_successful

local execute_unit_tests = function()
  unit_test_functions.print_msg("Starting " .. #unit_tests .. " unit tests...", 0)
  for unit_test_name, unit_test_func in pairs(unit_tests) do
    unit_test_functions.print_msg(string.format("Starting unit test %s.", unit_test_name), 0)
    local unit_test_result = unit_test_func()
    if unit_test_result == unit_test_functions.test_successful then
      unit_test_functions.print_msg(string.format("Unit test %s PASSED!", unit_test_name), 0)
    elseif unit_test_result == unit_test_functions.test_failed then -- soft failure
      unit_test_functions.print_msg(string.format("Unit test %s FAILED!", unit_test_name), 0)
      if unit_tests_result == unit_test_functions.test_successful then
        unit_tests_result = unit_test_functions.test_failed
      end
    elseif unit_test_result == unit_test_functions.test_invalid then -- hard failure
      unit_test_functions.print_msg(
        string.format("Unit test %s FAILED! Resolve issue(s) and rerun this test.", unit_test_name),
        0
      )
      unit_tests_result = unit_test_functions.test_invalid
      break
    else
      unit_test_functions.print_msg(string.format("Unexpected result for unit test %s!", unit_test_name), 0)
      break
    end
  end
  if unit_tests_result == unit_test_functions.test_successful then
    unit_test_functions.print_msg("Finished testing! All unit tests passed!", 0)
  else
    unit_test_functions.print_msg("Finished testing! Some unit tests failed!", 0)
  end
end

return execute_unit_tests
