#!/usr/bin/env ruby
# Advanced Ruby Gem Usage Example
# Combines multiple gems to process data

require 'json'
require 'csv'
require 'date'
require 'fileutils'
require 'digest'
require 'benchmark'

class DataProcessor
  attr_reader :results

  def initialize
    @results = []
    @stats = { processed: 0, errors: 0, time: 0 }
  end

  def process_csv_data
    puts "📊 Processing CSV Data..."

    csv_data = [
      ['ID', 'Name', 'Status', 'Date'],
      ['001', 'Search Query Fix', 'Complete', '2025-11-05'],
      ['002', 'Bug Fixes', 'Complete', '2025-11-05'],
      ['003', 'Ruby Integration', 'Active', '2025-11-05']
    ]

    # Generate CSV
    csv_string = CSV.generate do |csv|
      csv_data.each { |row| csv << row }
    end

    # Parse CSV back
    parsed = CSV.parse(csv_string, headers: true)
    parsed.each do |row|
      @results << row.to_h
      @stats[:processed] += 1
    end

    puts "✅ Processed #{@stats[:processed]} records"
  end

  def generate_report
    puts "\n📝 Generating JSON Report..."

    report = {
      timestamp: DateTime.now.iso8601,
      summary: @stats,
      data: @results,
      checksum: Digest::SHA256.hexdigest(@results.to_json)
    }

    json_report = JSON.pretty_generate(report)

    # Save to file
    output_dir = '/tmp/ruby_reports'
    FileUtils.mkdir_p(output_dir)

    output_file = File.join(output_dir, "report_#{Date.today}.json")
    File.write(output_file, json_report)

    puts "✅ Report saved to: #{output_file}"
    puts "\n📄 Report Preview:"
    puts json_report[0..500] + "..."

    output_file
  end

  def benchmark_operations
    puts "\n⏱️  Benchmarking Operations..."

    time = Benchmark.measure do
      1000.times do
        JSON.generate({ test: "data", number: rand(1000) })
      end
    end

    @stats[:time] = time.real
    puts "✅ 1000 JSON operations: #{time.real.round(4)}s"
  end
end

# Main execution
puts "🚀 Ruby Data Processor with Multiple Gems"
puts "=" * 70

processor = DataProcessor.new

# Run processing pipeline
processor.process_csv_data
processor.benchmark_operations
report_file = processor.generate_report

puts "\n" + "=" * 70
puts "✨ Processing Complete!"
puts "   Records: #{processor.results.size}"
puts "   Report: #{report_file}"
puts "=" * 70
