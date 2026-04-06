#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <unordered_map>
#include <string_view>
#include <vector>
#include <utility>

namespace py = pybind11;

struct ParsedRequest {
    std::string method;
    std::string path;
    std::unordered_map<std::string, std::string> headers;
};

ParsedRequest parse_http(const std::string& raw_request) {
    ParsedRequest req;
    std::string_view req_view(raw_request);

    size_t first_line_end = req_view.find("\r\n");
    if (first_line_end == std::string_view::npos) return req;

    std::string_view first_line = req_view.substr(0, first_line_end);
    
    size_t method_end = first_line.find(' ');
    if (method_end != std::string_view::npos) {
        req.method = std::string(first_line.substr(0, method_end));
        size_t path_end = first_line.find(' ', method_end + 1);
        if (path_end != std::string_view::npos) {
            req.path = std::string(first_line.substr(method_end + 1, path_end - method_end - 1));
        }
    }

    size_t header_start = first_line_end + 2;
    while (header_start < req_view.length()) {
        size_t line_end = req_view.find("\r\n", header_start);
        if (line_end == header_start || line_end == std::string_view::npos) break; 

        std::string_view line = req_view.substr(header_start, line_end - header_start);
        size_t colon_pos = line.find(':');
        
        if (colon_pos != std::string_view::npos) {
            std::string key = std::string(line.substr(0, colon_pos));
            size_t val_start = colon_pos + 1;
            while (val_start < line.length() && line[val_start] == ' ') val_start++;
            
            std::string val = std::string(line.substr(val_start));
            req.headers[key] = val;
        }
        header_start = line_end + 2;
    }

    return req;
}

py::bytes serialize_response(int status, const std::vector<std::pair<std::string, std::string>>& headers, const std::string& body) {
    std::string response;
    
    size_t estimated_size = 128 + body.size();
    for (const auto& h : headers) {
        estimated_size += h.first.size() + h.second.size() + 4;
    }
    response.reserve(estimated_size);

    response += "HTTP/1.1 " + std::to_string(status) + " OK\r\n";
    for (const auto& h : headers) {
        response += h.first + ": " + h.second + "\r\n";
    }
    response += "\r\n";
    response += body;

    return py::bytes(response);
}

PYBIND11_MODULE(fast_parser, m) {
    m.doc() = "High-performance C++ HTTP parser and serializer";

    py::class_<ParsedRequest>(m, "ParsedRequest")
        .def_readonly("method", &ParsedRequest::method)
        .def_readonly("path", &ParsedRequest::path)
        .def_readonly("headers", &ParsedRequest::headers);

    m.def("parse_http", &parse_http, "Parse raw HTTP request bytes");
    m.def("serialize_response", &serialize_response, "Fast HTTP response builder");
}