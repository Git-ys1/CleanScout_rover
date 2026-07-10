#include <librealsense2/rs.hpp>

#include <cstdlib>
#include <iostream>
#include <string>

int main(int argc, char **argv)
{
    try
    {
        const int fps = argc > 1 ? std::stoi(argv[1]) : 30;
        const bool low_power = argc > 2 && std::string(argv[2]) == "--low-power";

        rs2::context context;
        const rs2::device_list devices = context.query_devices();
        if (devices.size() == 0)
        {
            std::cerr << "no RealSense device detected" << std::endl;
            return EXIT_FAILURE;
        }

        const rs2::device device = devices.front();
        const std::string serial = device.get_info(RS2_CAMERA_INFO_SERIAL_NUMBER);
        if (low_power)
        {
            for (rs2::sensor sensor : device.query_sensors())
            {
                if (sensor.supports(RS2_OPTION_GLOBAL_TIME_ENABLED))
                    sensor.set_option(RS2_OPTION_GLOBAL_TIME_ENABLED, 0.0f);
                if (sensor.supports(RS2_OPTION_EMITTER_ENABLED))
                    sensor.set_option(RS2_OPTION_EMITTER_ENABLED, 0.0f);
            }
        }

        rs2::pipeline pipeline(context);
        rs2::config config;
        config.enable_device(serial);
        config.enable_stream(RS2_STREAM_DEPTH, 640, 480, RS2_FORMAT_Z16, fps);

        const rs2::pipeline_profile profile = pipeline.start(config);
        std::cout << "device="
                  << device.get_info(RS2_CAMERA_INFO_NAME)
                  << " serial="
                  << device.get_info(RS2_CAMERA_INFO_SERIAL_NUMBER)
                  << " firmware="
                  << device.get_info(RS2_CAMERA_INFO_FIRMWARE_VERSION)
                  << " fps=" << fps
                  << " low_power=" << (low_power ? "true" : "false")
                  << std::endl;

        for (int frame_index = 0; frame_index < 30; ++frame_index)
        {
            const rs2::frameset frames = pipeline.wait_for_frames(5000);
            const rs2::depth_frame depth = frames.get_depth_frame();
            if (!depth)
            {
                std::cerr << "missing depth frame at index " << frame_index << std::endl;
                return EXIT_FAILURE;
            }

            if ((frame_index % 5) == 0)
            {
                std::cout << "frame=" << frame_index
                          << " center_depth_m=" << depth.get_distance(320, 240)
                          << std::endl;
            }
        }

        pipeline.stop();
        std::cout << "RSUSB_DEPTH_SMOKE_OK" << std::endl;
        return EXIT_SUCCESS;
    }
    catch (const rs2::error &error)
    {
        std::cerr << "RealSense error: " << error.what() << std::endl;
    }
    catch (const std::exception &error)
    {
        std::cerr << "Error: " << error.what() << std::endl;
    }

    return EXIT_FAILURE;
}
