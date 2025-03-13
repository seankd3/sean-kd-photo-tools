# Changelog - SeanKD PhotoTools Suite

## [1.0.0] - 2025-03-13

### Added
- **Video Smover Module**
  - Implemented core functionality with three effects:
    - Motion Blur - Creates smooth motion trails
    - Timelapse - Compresses long videos into shorter clips
    - Slow Motion - Creates smooth slow-motion with frame interpolation
  - Added real-time video preview capabilities
  - Multi-threaded processing for improved UI responsiveness
  - Progress tracking and detailed status updates

- **Application Integration**
  - Created main PhotoToolsApp.py with modular architecture
  - Unified sidebar navigation for all modules
  - Integrated all modules in a single application:
    - DNG Stacker
    - Photo Desqueezer
    - GIF Creator
    - Video Averager
    - Video Smover
  
- **Settings & Theme Management**
  - Implemented theme switching (dark/light)
  - Added customizable accent colors
  - Created persistent settings with JSON storage
  - Added performance management options

- **Utilities**
  - Created ThemeManager for application-wide styling
  - Implemented SettingsManager for persistent preferences
  - Added ModuleBase class for common module functionality
  - Created unified error handling system

- **Application Launcher**
  - Added PhotoTools.pyw for easy startup
  - Implemented proper error handling and reporting
  - Added icon support for better desktop integration

### Technical Improvements
- Multi-threaded background processing for all intensive operations
- Modular architecture for easier future expansion
- Comprehensive error handling throughout the application
- Consistent UI/UX across all modules
