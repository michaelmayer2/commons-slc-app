libname trial "/tmp/trial" access=readonly;

/**
 * Mean response by treatment arm
 *
 * Averages the response score for each arm at one visit week.
 *
 * @measure arm_response
 * @param [week=12] `integer` Visit week: 0 for baseline, 12 for the end of treatment.
 * @return One row per arm, with the number of subjects and their mean response.
 * @output WORK.RESULT
 */
proc means data=trial.visits noprint nway;
  where week = &week;
  class arm;
  var response;
  output out=work.result(drop=_type_ _freq_) n=subjects mean=mean_response;
run;
