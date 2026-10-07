# Local only: line and branch coverage for a weride-api spec run. The repo has
# no coverage setup of its own (simplecov is only in the bundle through
# rubycritic), so the Tester loads this through RUBYOPT instead of editing
# spec_helper:
#
#   COV_FILES=app/commands/a.rb,app/policies/b.rb COV_DIR=<tmp>/cov \
#     RUBYOPT=-r$HOME/.claude/skills/team-lead/repos/weride-api.coverage.rb \
#     bundle exec rspec <spec paths>
#
# Prints one line per COV_FILES entry after the run, and writes the same lines
# to $COV_DIR/summary.txt. A file no spec loaded shows 0%.
require "simplecov"

COV_FILES = ENV.fetch("COV_FILES", "").split(",").map(&:strip).reject(&:empty?)

SimpleCov.root(Dir.pwd)
SimpleCov.coverage_dir(ENV.fetch("COV_DIR", "tmp/coverage"))
SimpleCov.enable_coverage :branch
SimpleCov.print_error_status = false
SimpleCov.formatter = Class.new { def format(_result) = nil }

SimpleCov.at_exit do
  by_path = SimpleCov.result.files.to_h { |file| [file.project_filename.delete_prefix("/"), file] }
  lines = COV_FILES.map do |path|
    file = by_path[path]
    next "#{path}: not tracked (outside app/ and lib/?)" unless file

    branches = file.total_branches.size
    branch_part = branches.zero? ? "no branches" : format("branches %d/%d", file.covered_branches.size, branches)
    format("%s: lines %.1f%% (%d/%d), %s, missed lines %s",
      path, file.covered_percent, file.covered_lines.size, file.lines_of_code, branch_part,
      file.missed_lines.map(&:line_number).inspect)
  end
  FileUtils.mkdir_p(SimpleCov.coverage_path)
  File.write(File.join(SimpleCov.coverage_path, "summary.txt"), lines.join("\n") + "\n")
  puts "", "Coverage:", *lines
end

SimpleCov.start do
  track_files "{app,lib}/**/*.rb"
  add_filter %w[/spec/ /config/ /db/ /vendor/]
end
