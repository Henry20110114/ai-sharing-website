// Renders the SVG sources in this folder to the PNGs the site uses, at exact pixel sizes.
// Run from the repo root:  swift assets/src/render-icons.swift
import AppKit

let root = URL(fileURLWithPath: CommandLine.arguments[0]).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
let jobs: [(svg: String, png: String, width: Int, height: Int)] = [
    ("favicon-32.svg", "favicon-32.png", 32, 32),
    ("apple-touch-icon.svg", "apple-touch-icon.png", 180, 180),
    ("og-image.svg", "og-image.png", 1200, 630),
]

for job in jobs {
    let svgPath = root.appendingPathComponent("assets/src/\(job.svg)").path
    let pngURL = root.appendingPathComponent("assets/\(job.png)")
    guard let image = NSImage(contentsOfFile: svgPath) else {
        print("cannot read \(svgPath)"); exit(1)
    }
    guard let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil, pixelsWide: job.width, pixelsHigh: job.height,
        bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
        colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0
    ) else { print("cannot create bitmap"); exit(1) }
    rep.size = NSSize(width: job.width, height: job.height)

    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    NSGraphicsContext.current?.imageInterpolation = .high
    image.draw(in: NSRect(x: 0, y: 0, width: job.width, height: job.height),
               from: .zero, operation: .sourceOver, fraction: 1.0)
    NSGraphicsContext.restoreGraphicsState()

    guard let data = rep.representation(using: .png, properties: [:]) else { print("cannot encode png"); exit(1) }
    do {
        try data.write(to: pngURL)
        print("wrote assets/\(job.png) \(job.width)x\(job.height)")
    } catch {
        print("cannot write \(pngURL.path): \(error)"); exit(1)
    }
}
