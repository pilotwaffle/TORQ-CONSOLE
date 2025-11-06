# Rakefile - Task automation for Ruby projects

require 'rake'
require 'json'
require 'fileutils'
require 'time'

# Default task
task :default => [:info]

# Display information
desc "Display Ruby environment information"
task :info do
  puts "\n🔧 Ruby Environment Info"
  puts "=" * 50
  puts "Ruby Version: #{RUBY_VERSION}"
  puts "Rake Version: #{Rake::VERSION}"
  puts "Working Dir:  #{Dir.pwd}"
  puts "=" * 50
end

# Run tests
desc "Run Ruby gem tests"
task :test do
  puts "\n🧪 Running Ruby Gem Tests..."
  sh "ruby test_ruby_gems.rb"
end

# Run data processor
desc "Run data processor example"
task :process do
  puts "\n📊 Running Data Processor..."
  sh "ruby ruby_data_processor.rb"
end

# Clean temporary files
desc "Clean temporary files and reports"
task :clean do
  puts "\n🧹 Cleaning temporary files..."
  FileUtils.rm_rf('/tmp/ruby_test_dir')
  FileUtils.rm_f('/tmp/ruby_test.log')
  FileUtils.rm_rf('/tmp/ruby_reports')
  puts "✅ Cleaned!"
end

# Generate summary report
desc "Generate summary report of all tests"
task :report do
  puts "\n📋 Generating Summary Report..."

  summary = {
    timestamp: Time.now.iso8601,
    ruby_version: RUBY_VERSION,
    rake_version: Rake::VERSION,
    tests_run: ['gem_tests', 'data_processor'],
    status: 'Complete'
  }

  report_file = 'ruby_test_summary.json'
  File.write(report_file, JSON.pretty_generate(summary))

  puts "✅ Summary saved to: #{report_file}"
  puts JSON.pretty_generate(summary)
end

# Run all tasks
desc "Run all tests and generate report"
task :all => [:test, :process, :report] do
  puts "\n✨ All tasks completed!"
end
