#!/usr/bin/env ruby
$PACKAGE_FILES = Dir["AtomicDatabase/*.py"]
$DEST          = "/opt/atomicdatabase/"
if ENV["USER"] != "root"
  puts "Can't run this command without root priviledges, it is supposed to install things!"
  exit 0
end
if ARGV.length >= 1 and ["install", "develop", "uninstall"].include? ARGV[0]
  case ARGV[0]
  when "install"
    puts "Installing Atomic Database..."
    unless File.directory? $DEST
      puts "Creating installation directory at #{$DEST}..."
      `mkdir #{$DEST}`
      puts "Directory created."
    else
      puts "Installation directory found at #{$DEST}"
    end
    puts "Installing required packages with pip:"
    File.foreach("requirements.txt").with_index do |line, line_num|
      `pip3 install #{line}`
    end
    puts "Installing Atomic Database code files..."
    $PACKAGE_FILES.each do |f|
      `cp #{f} #{$DEST}`
      puts "    Copied #{f}"
    end
    `cp atomicdb #{$DEST}`
    puts "    Copied atomicdb"
    puts "Creating executable in /usr/local/bin"
    `ln -s #{$DEST}atomicdb /usr/local/bin/`
    puts "Done!"
  when "develop"
    puts "Installing (Symlinked) Atomic Database..."
    unless File.directory? $DEST
      puts "Creating installation directory at #{$DEST}..."
      `mkdir #{$DEST}`
      puts "Directory created."
    else
      puts "Installation directory found at #{$DEST}"
    end
    puts "Installing required packages with pip:"
    File.foreach("requirements.txt").with_index do |line, line_num|
      `pip3 install #{line}`
    end
    puts "Installing Atomic Database code files..."
    $PACKAGE_FILES.each do |f|
      `ln -s #{Dir.pwd}/#{f} #{$DEST}`
      puts "    Linked #{f}"
    end

    puts "Linking excecutable in /usr/local/bin"
    `ln -s #{Dir.pwd}/atomicdb /usr/local/bin/atomicdb`
    puts "Done!"
  when "uninstall"
    puts "Uninstalling Atomic Database..."
    if File.directory? $DEST
      puts "Destroying directory at #{$DEST}..."
      `rm -rf #{$DEST}`
      puts "Directory destroyed."
    else
      puts "Installation directory not found at #{$DEST}. Are you sure Atomic Database is installed?"
    end
    puts "Removing executable in /usr/local/bin..."
    `rm -rf /usr/local/bin/atomicdb`
    puts "Done!"
  end
else
  puts "You need to supply setup.rb with a command to tell it what to do!\nAvailable commands:\n\n"
  commands = [
    {"name" => "install", "description" => "physically install Atomic Database (as atomicdb) to your computer"},
    {"name" => "develop", "description" => "symlink Atomic Database so it runs as if it were `install`ed"},
    {"name" => "uninstall", "description" => "undo all of the things develop or install did"}
  ]
  commands.each do |command|
    puts "    #{command["name"].ljust(15)} -- #{command["description"]}"
  end
  puts "\nChoose one of these commands please."
end
