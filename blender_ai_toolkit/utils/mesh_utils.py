"""Mesh quality analysis utilities for Blender meshes."""
import bpy
import bmesh
from typing import Dict, List, Optional


class MeshQualityAnalyzer:
    """Analyze mesh quality and report defects."""

    def __init__(self, obj: bpy.types.Object):
        if obj.type != 'MESH':
            raise ValueError("Object must be a mesh")
        self.obj = obj
        self.mesh = obj.data

    def analyze(self) -> Dict:
        """Run full mesh quality analysis."""
        bm = bmesh.new()
        bm.from_mesh(self.mesh)
        bm.ensure_lookup_tables()

        result = {
            "object_name": self.obj.name,
            "vertex_count": len(bm.verts),
            "face_count": len(bm.faces),
            "edge_count": len(bm.edges),
            "non_manifold_edges": self._count_non_manifold(bm),
            "loose_vertices": self._count_loose_verts(bm),
            "loose_edges": self._count_loose_edges(bm),
            "zero_area_faces": self._count_zero_area_faces(bm),
            "duplicate_vertices": self._count_duplicate_verts(bm),
            "wire_edges": self._count_wire_edges(bm),
            "ngons": self._count_ngons(bm),
            "triangles": self._count_triangles(bm),
            "quads": self._count_quads(bm),
            "poles_3": self._count_poles(bm, 3),
            "poles_5": self._count_poles(bm, 5),
            "poles_6plus": self._count_poles(bm, 6),
            "overlapping_faces": self._count_overlapping_faces(bm),
            "is_watertight": self._is_watertight(bm),
            "has_custom_normals": self.mesh.has_custom_normals,
            "stats": self._compute_stats(bm),
        }

        # Quality score (0-100)
        result["quality_score"] = self._compute_quality_score(result)

        bm.free()
        return result

    def _count_non_manifold(self, bm) -> int:
        """Count non-manifold edges."""
        count = 0
        for edge in bm.edges:
            if not edge.is_manifold:
                count += 1
        return count

    def _count_loose_verts(self, bm) -> int:
        """Count vertices not connected to any edge."""
        return sum(1 for v in bm.verts if not v.link_edges)

    def _count_loose_edges(self, bm) -> int:
        """Count edges with no connected faces."""
        return sum(1 for e in bm.edges if not e.link_faces)

    def _count_zero_area_faces(self, bm) -> int:
        """Count faces with zero or near-zero area."""
        count = 0
        for face in bm.faces:
            if face.calc_area() < 1e-6:
                count += 1
        return count

    def _count_duplicate_verts(self, bm) -> int:
        """Count duplicate vertices (same position)."""
        positions = {}
        count = 0
        for v in bm.verts:
            key = (round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6))
            if key in positions:
                count += 1
            else:
                positions[key] = True
        return count

    def _count_wire_edges(self, bm) -> int:
        """Count edges with only one connected face (boundary) or no faces."""
        return sum(1 for e in bm.edges if len(e.link_faces) < 2)

    def _count_ngons(self, bm) -> int:
        """Count faces with more than 4 vertices."""
        return sum(1 for f in bm.faces if len(f.verts) > 4)

    def _count_triangles(self, bm) -> int:
        """Count triangular faces."""
        return sum(1 for f in bm.faces if len(f.verts) == 3)

    def _count_quads(self, bm) -> int:
        """Count quad faces."""
        return sum(1 for f in bm.faces if len(f.verts) == 4)

    def _count_poles(self, bm, n: int) -> int:
        """Count vertices with exactly n connected edges."""
        if n < 6:
            return sum(1 for v in bm.verts if len(v.link_edges) == n)
        return sum(1 for v in bm.verts if len(v.link_edges) >= n)

    def _count_overlapping_faces(self, bm) -> int:
        """Count faces that overlap (same plane, same position)."""
        # Simplified: check for faces with same center and normal
        seen = {}
        count = 0
        for face in bm.faces:
            center = face.calc_center_median()
            normal = face.normal
            key = (
                round(center.x, 4), round(center.y, 4), round(center.z, 4),
                round(normal.x, 4), round(normal.y, 4), round(normal.z, 4),
            )
            if key in seen:
                count += 1
            else:
                seen[key] = True
        return count

    def _is_watertight(self, bm) -> bool:
        """Check if mesh is watertight (all edges have exactly 2 faces)."""
        return all(len(e.link_faces) == 2 for e in bm.edges)

    def _compute_stats(self, bm) -> Dict:
        """Compute general statistics."""
        areas = [f.calc_area() for f in bm.faces]
        lengths = [e.calc_length() for e in bm.edges]

        return {
            "total_area": sum(areas),
            "avg_face_area": sum(areas) / len(areas) if areas else 0,
            "min_face_area": min(areas) if areas else 0,
            "max_face_area": max(areas) if areas else 0,
            "avg_edge_length": sum(lengths) / len(lengths) if lengths else 0,
            "min_edge_length": min(lengths) if lengths else 0,
            "max_edge_length": max(lengths) if lengths else 0,
        }

    def _compute_quality_score(self, result: Dict) -> int:
        """Compute a quality score from 0 (worst) to 100 (best)."""
        score = 100

        # Deductions for issues
        v_count = max(result["vertex_count"], 1)
        f_count = max(result["face_count"], 1)

        score -= min(20, (result["non_manifold_edges"] / v_count) * 100)
        score -= min(15, (result["loose_vertices"] / v_count) * 100)
        score -= min(10, (result["zero_area_faces"] / f_count) * 100)
        score -= min(10, (result["duplicate_vertices"] / v_count) * 100)
        score -= min(5, (result["ngons"] / f_count) * 100)
        score -= min(5, (result["overlapping_faces"] / f_count) * 100)

        if not result["is_watertight"]:
            score -= 10

        return max(0, min(100, int(score)))


def analyze_mesh(obj: bpy.types.Object) -> Dict:
    """Convenience function to analyze a mesh object."""
    analyzer = MeshQualityAnalyzer(obj)
    return analyzer.analyze()


def get_quality_report(obj: bpy.types.Object) -> str:
    """Get a formatted quality report string."""
    result = analyze_mesh(obj)

    lines = [
        f"Mesh Quality Report: {result['object_name']}",
        f"{'=' * 50}",
        f"Quality Score: {result['quality_score']}/100",
        f"",
        f"Geometry:",
        f"  Vertices: {result['vertex_count']}",
        f"  Edges: {result['edge_count']}",
        f"  Faces: {result['face_count']}",
        f"  Triangles: {result['triangles']}",
        f"  Quads: {result['quads']}",
        f"  N-gons: {result['ngons']}",
        f"",
        f"Topology Issues:",
        f"  Non-manifold edges: {result['non_manifold_edges']}",
        f"  Loose vertices: {result['loose_vertices']}",
        f"  Loose edges: {result['loose_edges']}",
        f"  Zero-area faces: {result['zero_area_faces']}",
        f"  Duplicate vertices: {result['duplicate_vertices']}",
        f"  Overlapping faces: {result['overlapping_faces']}",
        f"",
        f"Edge Distribution:",
        f"  3-edge poles: {result['poles_3']}",
        f"  5-edge poles: {result['poles_5']}",
        f"  6+ edge poles: {result['poles_6plus']}",
        f"",
        f"Properties:",
        f"  Watertight: {'Yes' if result['is_watertight'] else 'No'}",
        f"  Custom normals: {'Yes' if result['has_custom_normals'] else 'No'}",
        f"",
        f"Dimensions:",
        f"  Total area: {result['stats']['total_area']:.4f}",
        f"  Avg face area: {result['stats']['avg_face_area']:.6f}",
        f"  Avg edge length: {result['stats']['avg_edge_length']:.4f}",
    ]

    return "\n".join(lines)
