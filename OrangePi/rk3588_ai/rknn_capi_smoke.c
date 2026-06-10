#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "rknn_api.h"

static void *read_file(const char *path, uint32_t *size_out) {
    FILE *file = fopen(path, "rb");
    long size;
    void *data;

    if (file == NULL) {
        perror("fopen");
        return NULL;
    }
    if (fseek(file, 0, SEEK_END) != 0 || (size = ftell(file)) <= 0 ||
        size > UINT32_MAX || fseek(file, 0, SEEK_SET) != 0) {
        fprintf(stderr, "failed to determine model size: %s\n", path);
        fclose(file);
        return NULL;
    }

    data = malloc((size_t)size);
    if (data == NULL) {
        perror("malloc");
        fclose(file);
        return NULL;
    }
    if (fread(data, 1, (size_t)size, file) != (size_t)size) {
        fprintf(stderr, "failed to read complete model: %s\n", path);
        free(data);
        fclose(file);
        return NULL;
    }

    fclose(file);
    *size_out = (uint32_t)size;
    return data;
}

int main(int argc, char **argv) {
    rknn_context context = 0;
    rknn_sdk_version version = {0};
    rknn_input_output_num io_num = {0};
    uint32_t model_size = 0;
    void *model;
    int ret;

    if (argc != 2) {
        fprintf(stderr, "usage: %s MODEL.rknn\n", argv[0]);
        return 2;
    }

    model = read_file(argv[1], &model_size);
    if (model == NULL) {
        return 2;
    }

    printf("model=%s size=%u\n", argv[1], model_size);
    fflush(stdout);
    ret = rknn_init(&context, model, model_size, 0, NULL);
    printf("rknn_init ret=%d context=%llu\n", ret,
           (unsigned long long)context);
    fflush(stdout);
    free(model);
    if (ret != RKNN_SUCC) {
        return 1;
    }

    ret = rknn_query(context, RKNN_QUERY_SDK_VERSION, &version,
                     sizeof(version));
    printf("RKNN_QUERY_SDK_VERSION ret=%d api=%s driver=%s\n", ret,
           version.api_version, version.drv_version);

    ret = rknn_query(context, RKNN_QUERY_IN_OUT_NUM, &io_num,
                     sizeof(io_num));
    printf("RKNN_QUERY_IN_OUT_NUM ret=%d inputs=%u outputs=%u\n", ret,
           io_num.n_input, io_num.n_output);

    ret = rknn_destroy(context);
    printf("rknn_destroy ret=%d\n", ret);
    return ret == RKNN_SUCC ? 0 : 1;
}
