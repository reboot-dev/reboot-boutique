# Resemble <-> React Example

This directory is meant to bootstrap a fullstack, Resemble applications.

## Steps to Create a New Fullstack App

1. Copy and rename `/resemble_react_example`.
2. Update and rename `/resemble_react_your_app/pingpong.proto`. Don’t forget
   to update the `package` also.
   NOTE: `.reader` methods MUST be annotated with `get` and writer methods must be
   annotated with `post`. Also the method path MUST match the method name:

```proto
option (google.api.http) = {
    get: “/SameAsReaderMethodName”
}
option (google.api.http) = {
    post: “/SameAsWriterMethodName”
}
```

3. Update `/resemble_react_your_app/BUILD.bazel` to build the new `.proto`, and
   remember to update the file path `“//resemble_react_your_app_name”` as well.
4. Update and rename files and folder `/resemble_react_your_app_name/backend`.
5. Change symlink in `/resemble_react_your_app_name/web/proto/pingpong.proto` to the proto in your `/api` folder.
6. Update `resemble_react_your_app_name/BUILD.bazel`.
7. Open three separate terminals.
8. `ibazel run resemble_react_your_app_name:gen_ts`
9. `ibazel build resemble_react_your_app_name/backend:app_name_zip`
10. `./rsm.sh dev --name your_app --no-chaos --fullstack --package-json your_resemble_app/web/package.json --python bazel-bin/your_resemble_app/backend/app_name.zip`
